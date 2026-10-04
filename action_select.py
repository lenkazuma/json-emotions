"""Turn free-form instructions (Chinese or English) into one robot arm action."""

import os

import streamlit as st
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from chat_core import ACTIONS, DEFAULT_MODEL, NO_ACTION, choose_action

PRESET_INSTRUCTIONS = [
    "请你挥挥手",
    "你能点点头吗",
    "Can you rotate around",
    "Can you jump?",
    "眨眨眼吧",
    "你能讲话不",
]


def main():
    load_dotenv(find_dotenv(), override=False)
    st.set_page_config(page_title="Robot Arm Commands", page_icon="🤖")
    st.subheader("下达机械臂指令")
    st.caption("Supported actions: " + ", ".join(f"`{a}`" for a in ACTIONS))

    with st.sidebar:
        api_key = st.text_input(
            "OpenAI API key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="Kept only in this browser session. Defaults to OPENAI_API_KEY from the environment.",
        )
        model = st.selectbox("Model", [DEFAULT_MODEL, "gpt-4o", "gpt-4.1-mini"])

    st.session_state.setdefault("actions", [])

    clicked = None
    cols = st.columns(3)
    for i, instruction in enumerate(PRESET_INSTRUCTIONS):
        if cols[i % 3].button(instruction, width="stretch"):
            clicked = instruction
    instruction = st.chat_input("Instruction") or clicked

    if instruction:
        if not api_key:
            st.warning("Enter an OpenAI API key in the sidebar first.")
        else:
            try:
                action = choose_action(OpenAI(api_key=api_key), instruction, model)
            except Exception as exc:  # noqa: BLE001 - surface API errors in the UI
                st.error(f"OpenAI request failed: {exc}")
            else:
                st.session_state.actions.append((instruction, action))

    for instruction, action in reversed(st.session_state.actions):
        with st.chat_message("user"):
            st.markdown(instruction)
        with st.chat_message("assistant"):
            if action == NO_ACTION:
                st.markdown("No supported action found in this instruction.")
            else:
                st.markdown(f"Action: **{action}** ({ACTIONS[action]}) → run `{action}.py`")


if __name__ == "__main__":
    main()
