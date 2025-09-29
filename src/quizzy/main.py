from pathlib import Path
from base64 import b64decode, b64encode
import json
from typing import List

from nicegui import ui, events

from Quiz import Quiz


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


active_color = "blue"
inactive_color = "grey"


def on_click(user_results: FilledQuiz, page: int):
    def callback(e: events.ClickEventArguments):
        sans = user_results.serialize_answers()
        ui.navigate.to(f"/run/{user_results.name}?page={page}&answers={sans}", new_tab=False)

    return callback


def on_submit(user_results: FilledQuiz):
    def callback(e: events.ClickEventArguments):
        sans = user_results.serialize_answers()
        ui.navigate.to(f"/results/{user_results.name}?answers={sans}", new_tab=False)

    return callback


@ui.page("/results/{quizz}")
def display_results(quizz: str, answers: str):
    qpth = Path(f"quizzes/{quizz}.yml")
    user_results = FilledQuiz.from_yaml(qpth)
    user_results.set_answers_from_serialzed(answers)

    columns = [
        {"label": "Question", "field": "question", "align": "left"},
        {"label": "Verdict", "field": "verdict", "align": "center"},
    ]
    rows = []

    count_ok = 0
    count_total = 0
    for q, sans in zip(user_results.questions, user_results.extract_answers()):
        verdict = set(q.good_answers) == set(sans)
        count_ok += 1 if verdict else 0
        count_total += 1
        symb = "✅" if verdict else "❌"
        rows.append({"question": q.text, "verdict": symb})  # type: ignore

    score = int(100 * count_ok / count_total)

    with ui.column():
        ui.markdown("# Résultats")
        ui.table(columns=columns, rows=rows, row_key="question")
        ui.markdown(f"### Bonnes réponses : {score}%")

        for score_key in user_results.echelle_scores.keys():
            if score >= score_key:
                ui.markdown(f"#### {user_results.echelle_scores[score_key]}")
                break


@ui.page("/run/{quizz}")
def run_quizz(quizz: str, page: int | None = None, answers: str = ""):
    qpth = Path(f"quizzes/{quizz}.yml")
    user_results = FilledQuiz.from_yaml(qpth)

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


@ui.page("/accueil/{quizz}")
def accueil_quizz(quizz: str):
    qpth = Path(f"quizzes/{quizz}.yml")
    user_results = FilledQuiz.from_yaml(qpth)

    with ui.column():
        ui.markdown(f"# {user_results.message_accueil}")

        ui.button(
            user_results.text_bouton, on_click=lambda: ui.navigate.to(f"/run/{user_results.name}")
        )


ui.run(title="Quizzy", reload=True, port=8030)
