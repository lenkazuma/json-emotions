"""Chat with Mrs Fox: each reply is paired with a Lottie animation chosen by the model."""

import os

import streamlit as st
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI
from streamlit_lottie import st_lottie

from chat_core import DEFAULT_MODEL, ask, choose_animation, load_animation

PRESET_QUESTIONS = [
    "13.8比13.11大吗？",
    "能介绍一下你自己吗？",
    "我觉得宇宙是无边界的，你说对吗？",
    "1+1=3，对吗？",
    "能恭喜一下我吗",
]
MODELS = [DEFAULT_MODEL, "gpt-4o", "gpt-4.1-mini", "gpt-4.1"]


@st.cache_data(show_spinner=False)
def cached_animation(animation_id):
    return load_animation(animation_id)


def render_message(index, message):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] != "assistant":
            return
        data = cached_animation(message.get("animation")) if message.get("animation") else None
        if data:
            st_lottie(data, height=260, key=f"lottie-{index}")
        st.feedback("thumbs", key=f"feedback-{index}")


def handle_question(client, model, question):
    history = list(st.session_state.history)
    st.session_state.history.append({"role": "user", "content": question})
    try:
        with st.spinner("Mrs Fox is thinking..."):
            answer = ask(client, history, question, model)
            animation = choose_animation(client, question, answer, model)
    except Exception as exc:  # noqa: BLE001 - surface API errors in the UI
        st.session_state.history.pop()
        st.error(f"OpenAI request failed: {exc}")
        return
    st.session_state.history.append({"role": "assistant", "content": answer, "animation": animation})


def main():
    load_dotenv(find_dotenv(), override=False)
    st.set_page_config(page_title="Chatbot With Animations", page_icon="🦊")
    st.subheader("🦊 AI chat with Lottie animations")

    with st.sidebar:
        api_key = st.text_input(
            "OpenAI API key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="Kept only in this browser session. Defaults to OPENAI_API_KEY from the environment.",
        )
        model = st.selectbox("Model", MODELS)
        if st.button("Clear chat"):
            st.session_state.history = []

    st.session_state.setdefault("history", [])

    clicked = None
    cols = st.columns(len(PRESET_QUESTIONS))
    for col, question in zip(cols, PRESET_QUESTIONS):
        if col.button(question, width="stretch"):
            clicked = question
    typed = st.chat_input("Your question")
    question = typed or clicked

    if question:
        if not api_key:
            st.warning("Enter an OpenAI API key in the sidebar first.")
        else:
            handle_question(OpenAI(api_key=api_key), model, question)

    for index, message in enumerate(st.session_state.history):
        render_message(index, message)


if __name__ == "__main__":
    main()
