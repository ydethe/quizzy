from pathlib import Path
import gradio as gr

from quizzy.Quiz import Quiz


def load_quiz(request: gr.Request) -> Quiz:
    # Path
    path: str = request.path
    print(path)
    quiz = Quiz.from_yaml(Path(path))

    # # Query parameters
    # parsed = urlparse(url)
    # query_params = parse_qs(parsed.query)

    return quiz


def next_page(curr_page, name, age, email):
    # Save answers progressively
    state = {"name": name, "age": age, "email": email}
    next_page = curr_page + 1
    return (
        next_page,
        gr.update(visible=next_page == 0),
        gr.update(visible=next_page == 1),
        gr.update(visible=next_page == 2),
        state,
    )


# def prev_page(curr_page, name, age, email):
#     state = {"name": name, "age": age, "email": email}
#     prev_page = max(0, curr_page - 1)
#     return prev_page, gr.update(visible=prev_page==0), gr.update(visible=prev_page==1), gr.update(visible=prev_page==2), state


def submit(name, age, email):
    return f"✅ Thanks {name}, age {age}, contact {email}"


with gr.Blocks() as demo:
    curr_page = gr.State(0)
    answers = gr.State({})

    with gr.Column(visible=True) as page1:
        name = gr.Textbox(label="What's your name?")
        next1 = gr.Button("Next ➡️")

    with gr.Column(visible=False) as page2:
        age = gr.Number(label="How old are you?")
        # prev2 = gr.Button("⬅️ Back")
        next2 = gr.Button("Next ➡️")

    with gr.Column(visible=False) as page3:
        email = gr.Textbox(label="What's your email?")
        # prev3 = gr.Button("⬅️ Back")
        submit_btn = gr.Button("Submit")
        output = gr.Textbox(label="Result")

    # Navigation logic
    next1.click(next_page, [curr_page, name, age, email], [curr_page, page1, page2, page3, answers])
    next2.click(next_page, [curr_page, name, age, email], [curr_page, page1, page2, page3, answers])
    # prev2.click(prev_page, [curr_page, name, age, email], [curr_page, page1, page2, page3, answers])
    # prev3.click(prev_page, [curr_page, name, age, email], [curr_page, page1, page2, page3, answers])

    submit_btn.click(submit, [name, age, email], output)

demo.launch()
