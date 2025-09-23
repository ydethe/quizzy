import streamlit as st

from quizzy.Quiz import Quiz


st.title("Uber pickups in NYC")

# Read query params (?name=Alice&age=30)
params = st.query_params
quiz = Quiz.from_yaml(params.get("q"))

if "step" not in st.session_state:
    st.session_state.step = 0

# Use the get method since the keys won't be in session_state
# on the first script run
if st.session_state.get("answer_00"):
    st.session_state["user_answer"] = "0"

if st.session_state.get("answer_01"):
    st.session_state["user_answer"] = "1"

if st.session_state.get("answer_02"):
    st.session_state["user_answer"] = "2"

if st.session_state.get("answer_03"):
    st.session_state["user_answer"] = "3"


c = st.container()

question = quiz.questions[st.session_state.step]

c.title(question.text)

# c.text_input("Name", key="user_answer")

for k, a in enumerate(question.answers):
    c.button(a, key=f"answer_{k:02}")

if c.button("Suivant"):
    st.session_state.step += 1
