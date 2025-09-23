from pathlib import Path
from nicegui import ui, events
from fastapi import Request

from quizzy.Quiz import Quiz


class Results:
    def __init__(self):
        self.answers = dict()

    def reset(self, number_of_answers: int):
        self.answers = {idx: False for idx in range(number_of_answers)}

    def on_chip_click(self, idx: int):
        def callback(e: events.ClickEventArguments):
            self.answers[idx] = self.update_color(e)

        return callback

    def update_color(self, e: events.ClickEventArguments) -> bool:
        color = e.sender._props.get("color", active_color)
        state = color == inactive_color
        e.sender.props(f"color={active_color if state else inactive_color}")

        return state


user_results = Results()

active_color = "blue"
inactive_color = "grey"


def on_click(quizz, page):
    def callback(e: events.ClickEventArguments):
        print(user_results.answers)
        ui.navigate.to(f"{quizz}?page={page}", new_tab=False)

    return callback


@ui.page("/{quizz}")
def hello_page(request: Request, quizz: str, page: int | None = None):
    qpth = Path(f"tests/{quizz}.yml")
    qo = Quiz.from_yaml(qpth)

    if page is None:
        page = 0

    if page >= qo.number_of_questions:
        page = qo.number_of_questions - 1

    question = qo.questions[page]

    user_results.reset(question.number_of_answers)

    with ui.column():
        ui.markdown(f"# {question.text}")

        for idx, a in enumerate(question.answers):
            ui.chip(a, on_click=user_results.on_chip_click(idx)).props(f"color={inactive_color}")

        with ui.button_group():
            if page > 0:
                ui.button("Précédent", on_click=on_click(quizz, page - 1))
            ui.button("Suivant", on_click=on_click(quizz, page + 1))


ui.run(port=3000)
