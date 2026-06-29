import streamlit as st
from components.chat import render_chat_history


def render_conversation_detail(conversation_data: dict):
    """
    Renders the details of a single conversation, including its history.
    """
    title = conversation_data.get("title", "Untitled Conversation")
    st.subheader(title)

    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Created: {conversation_data.get('created_at')}")
    with col2:
        st.caption(f"Updated: {conversation_data.get('updated_at')}")

    messages = conversation_data.get("messages", [])
    st.markdown(f"**Total Messages:** {len(messages)}")

    st.divider()

    # Map the 'importance' field if available to a UI element? We'll just show chat.
    # Convert 'user' / 'assistant' correctly.
    chat_history = []
    for m in messages:
        chat_history.append(
            {"role": m.get("role", "user"), "content": m.get("content", "")}
        )

    # Render using the chat component
    render_chat_history(chat_history)
