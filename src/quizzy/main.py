import streamlit as st


st.title("Uber pickups in NYC")

# Use the get method since the keys won't be in session_state
# on the first script run
if st.session_state.get("answer_01"):
    st.session_state["user_answer"] = "0"
if st.session_state.get("answer_02"):
    st.session_state["user_answer"] = "1"

st.text_input("Name", key="user_answer")

st.button("Answer 01", key="answer_01")
st.button("Answer 02", key="answer_02")
