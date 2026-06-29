import streamlit as st


def render_chat_message(role: str, content: str):
    """
    Renders a single chat message.
    Role should be 'user' or 'assistant'.
    """
    with st.chat_message(role):
        st.markdown(content)


def render_chat_history(history: list):
    """
    history: list of dicts with 'role' and 'content'
    """
    for msg in history:
        render_chat_message(msg["role"], msg["content"])
