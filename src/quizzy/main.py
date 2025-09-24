from pathlib import Path
from base64 import b64decode,b64encode
import json

from nicegui import ui, events
from fastapi import Request

from quizzy.Quiz import Quiz


class FilledQuiz(Quiz):
    def on_chip_click(self, page:int,idx: int):
        def callback(e: events.ClickEventArguments):
            status=self.update_color(e)
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

    def serialize_answers(self)->str:
        uans=[list(a.user_answers) for a in self.questions]
        jans=json.dumps(uans).encode('utf-8')
        return b64encode(jans).decode('utf-8')

    def set_answers_from_serialzed(self,answers:str):
        sans=b64decode(answers)
        ans_obj=json.loads(sans)
        for page,qans in enumerate(ans_obj):
            self.questions[page].user_answers=set()
            for idx in qans:
                self.questions[page].user_answers.add(idx)

active_color = "blue"
inactive_color = "grey"


def on_click(quizz:FilledQuiz, page:int):
    def callback(e: events.ClickEventArguments):
        sans=quizz.serialize_answers()
        ui.navigate.to(f"{quizz.name}?page={page}&answers={sans}", new_tab=False)

    return callback

def on_submit(user_results:FilledQuiz):
    def callback(e: events.ClickEventArguments):
        print(user_results.serialize_answers())
    return callback

@ui.page("/{quizz}")
def hello_page(request: Request, quizz: str, page: int | None = None, answers: str =""):
    qpth = Path(f"tests/{quizz}.yml")
    user_results = FilledQuiz.from_yaml(qpth)

    if answers!="":
        user_results.set_answers_from_serialzed(answers)

    if page is None:
        page = 0

    if page >= user_results.number_of_questions:
        page = user_results.number_of_questions - 1

    question = user_results.questions[page]

    with ui.column():
        ui.markdown(f"# {question.text}")

        for idx, answer_text in enumerate(question.answers):
            color = active_color if idx in question.user_answers else inactive_color
            ui.chip(answer_text, on_click=user_results.on_chip_click(page,idx)).props(f"color={color}")

        with ui.button_group():
            if page > 0:
                ui.button("Précédent", on_click=on_click(user_results, page - 1))

            if page <user_results.number_of_questions-1:
                ui.button("Suivant", on_click=on_click(user_results, page + 1))
            else:
                ui.button("Soumettre", on_click=on_submit(user_results))

ui.run(port=3000)
