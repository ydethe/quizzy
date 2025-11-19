from datetime import datetime
from pathlib import Path
from base64 import b64decode, b64encode
import json
from typing import List

from fastapi.responses import RedirectResponse
from fastapi_sso import OpenID
from sqlmodel import select, Session
import uvicorn
from fastapi import Depends, FastAPI, Request, Response
from nicegui import Client, ui, events
from starlette.middleware.sessions import SessionMiddleware

from .Quiz import Quiz
from .database import Passage, engine, Etudiant
from .config import config, Examen
from . import logger
from .auth import auth_router, get_logged_user, RequiresLoginException


fastapi_app = FastAPI()
fastapi_app.add_middleware(SessionMiddleware, secret_key=config.JWT_SECRET)

fastapi_app.include_router(auth_router)


@fastapi_app.exception_handler(RequiresLoginException)
async def exception_handler(request: Request, exc: RequiresLoginException) -> Response:
    return RedirectResponse(url="/auth/login")


class FilledQuiz(Quiz):
    def on_chip_click(self, page: int, idx: int):
        def callback(e: events.ClickEventArguments):
            status = self.update_color(e)
            if status:
                self.questions[page].user_answers.add(idx)
            else:
                self.questions[page].user_answers.remove(idx)

        return callback

    def update_color(self, e: events.ClickEventArguments) -> bool:
        color = e.sender._props.get("color", active_color)
        state = color == inactive_color
        e.sender.props(f"color={active_color if state else inactive_color}")

        return state

    def extract_answers(self) -> List[List[int]]:
        uans = [list(a.user_answers) for a in self.questions]
        return uans

    def serialize_answers(self) -> str:
        uans = self.extract_answers()
        jans = json.dumps(uans).encode("utf-8")
        return b64encode(jans).decode("utf-8")

    def decode_answer(self, answers: str) -> str:
        sans = b64decode(answers)
        ans_obj = json.loads(sans)
        return ans_obj

    def set_answers_from_serialzed(self, answers: str):
        ans_obj = self.decode_answer(answers)
        for page, qans in enumerate(ans_obj):
            self.questions[page].user_answers = set()
            for idx in qans:
                self.questions[page].user_answers.add(idx)

    def get_score(self) -> float:
        count_ok = 0
        count_total = 0
        for q, sans in zip(self.questions, self.extract_answers()):
            verdict = set(q.good_answers) == set(sans)
            count_ok += 1 if verdict else 0
            count_total += 1

        score = int(100 * count_ok / count_total)

        return score


active_color = "blue"
inactive_color = "grey"


def enregistre_examen(examen: Examen, quizz: FilledQuiz, client_ip: str):
    with Session(engine) as session:
        query = select(Etudiant).where(Etudiant.email == examen.email)
        results = session.exec(query).all()

        # query = select(e for e in Etudiant if e.email == examen.email)
        if len(results) == 0:
            e = Etudiant(nom=examen.nom, prenom=examen.prenom, email=examen.email)
            session.add(e)
        else:
            e = results[0]

        Passage(
            quiz_nom=examen.quizz,
            quiz_hash=quizz.hash,
            etudiant_id=e.id,
            date=datetime.now(),
            reponses=quizz.serialize_answers(),
            score=quizz.get_score(),
            ip_origine=client_ip,
        )


def on_click(user_results: FilledQuiz, page: int):
    def callback(e: events.ClickEventArguments):
        sans = user_results.serialize_answers()
        ui.navigate.to(f"/run?token={user_results.token}&page={page}&answers={sans}", new_tab=False)

    return callback


def on_submit(user_results: FilledQuiz):
    def callback(e: events.ClickEventArguments):
        sans = user_results.serialize_answers()
        ui.navigate.to(f"/results?token={user_results.token}&answers={sans}", new_tab=False)

    return callback


@fastapi_app.get("/health")
def health_check():
    return {"status": "healthy"}


@ui.page("/admin")
def display_admin(user: OpenID = Depends(get_logged_user)):
    qpth = Path("quizzes")
    choices = []
    for file in qpth.glob("*.yml"):
        quizz_name = file.stem
        choices.append(quizz_name)

    ui.markdown("# Administration\n## Création d'un lien")
    select = ui.select(choices, label="Nom du quiz", value=choices[0])
    nom = ui.input(label="Nom")
    prenom = ui.input(label="Prénom")
    email = ui.input(label="Email")

    token_label = ui.label()

    class _link_data:
        def __init__(self):
            self.token = ""

        def on_create(self, e: events.ClickEventArguments):
            if select.value is None or email.value == "" or nom.value == "" or prenom.value == "":
                ui.notify("Remplir le questionnaire")
                return

            exam = Examen(quizz=select.value, email=email.value, nom=nom.value, prenom=prenom.value)

            m = exam.get_encrypted()

            token_label.set_text(m)
            self.token = m
            goto_btn.enable()

        def on_goto(self, e: events.ClickEventArguments):
            ui.navigate.to(f"/accueil?token={self.token}")

    ld = _link_data()

    with ui.button_group():
        ui.button("Créer lien", on_click=ld.on_create)
        goto_btn = ui.button("Aller au quiz", on_click=ld.on_goto)
        goto_btn.disable()


@ui.page("/results")
async def display_results(client: Client, token: str, answers: str):
    await client.connected()
    client_ip: str = client.environ["asgi.scope"]["client"][0]

    examen = Examen.from_encrypted(token)
    quizz = examen.quizz
    qpth = Path(f"quizzes/{quizz}.yml")
    user_results = FilledQuiz.from_yaml(qpth)
    user_results.set_answers_from_serialzed(answers)
    user_results.token = token

    columns = [
        {"label": "Question", "field": "question", "align": "left"},
        {"label": "Verdict", "field": "verdict", "align": "center"},
    ]
    rows = []

    for q, sans in zip(user_results.questions, user_results.extract_answers()):
        verdict = set(q.good_answers) == set(sans)
        symb = "✅" if verdict else "❌"
        rows.append({"question": q.text, "verdict": symb})  # type: ignore

    score = user_results.get_score()

    with ui.column():
        ui.markdown("# Résultats")
        ui.table(columns=columns, rows=rows, row_key="question")
        ui.markdown(f"### Bonnes réponses : {score}%")

        for score_key in user_results.echelle_scores.keys():
            if score >= score_key:
                ui.markdown(f"#### {user_results.echelle_scores[score_key]}")
                break

    enregistre_examen(examen, user_results, client_ip)
    logger.info(
        f"Exam taken: {examen.prenom} {examen.nom} <{examen.email}> @ {client_ip} - answers: {user_results.serialize_answers()} - token: {user_results.token} - score: {user_results.get_score()}"
    )


@ui.page("/run")
def run_quizz(token: str, page: int | None = None, answers: str = ""):
    examen = Examen.from_encrypted(token)
    quizz = examen.quizz

    qpth = Path(f"quizzes/{quizz}.yml")
    user_results = FilledQuiz.from_yaml(qpth)
    user_results.token = token

    if answers != "":
        user_results.set_answers_from_serialzed(answers)

    if page is None:
        page_num = 0
    else:
        page_num = page

    question = user_results.questions[page_num]

    with ui.column():
        ui.markdown(f"# {question.text}")

        for idx, answer_text in enumerate(question.answers):
            color = active_color if idx in question.user_answers else inactive_color
            ui.chip(answer_text, on_click=user_results.on_chip_click(page_num, idx)).props(
                f"color={color}"
            )

        with ui.button_group():
            if page_num > 0:
                ui.button("Précédent", on_click=on_click(user_results, page_num - 1))

            if page_num < user_results.number_of_questions - 1:
                ui.button("Suivant", on_click=on_click(user_results, page_num + 1))
            else:
                ui.button("Soumettre", on_click=on_submit(user_results))


@ui.page("/accueil")
def accueil_quizz(token: str):
    examen = Examen.from_encrypted(token)

    quizz = examen.quizz
    qpth = Path(f"quizzes/{quizz}.yml")
    user_results = FilledQuiz.from_yaml(qpth)
    user_results.token = token

    with ui.column():
        ui.markdown(user_results.message_accueil.format(prenom=examen.prenom))

        ui.button(
            user_results.text_bouton,
            on_click=lambda: ui.navigate.to(f"/run?token={user_results.token}"),
        )


ui.run_with(
    fastapi_app,
    title="Quizzy",
    favicon="🎓",
    storage_secret="pick your private secret here",  # NOTE setting a secret is optional but allows for persistent storage per user
)

if __name__ == "__main__":
    uvicorn.run(
        "quizzy.__main__:fastapi_app", host="0.0.0.0", port=8000, log_level="info", reload=False
    )
