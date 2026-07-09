import streamlit as st
import uuid
from services.api_client import api_client


def render_sidebar():
    # Initialize Session State Variables for all pages
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "trace" not in st.session_state:
        st.session_state.trace = []
    if "metrics" not in st.session_state:
        st.session_state.metrics = {}
    if "sources" not in st.session_state:
        st.session_state.sources = []

    with st.sidebar:
        st.title("Enterprise AI Operations")
        st.caption("Autonomous Enterprise Manager")

        st.divider()

        # Backend Health
        try:
            health = api_client.health()
            if health.get("status") == "healthy":
                st.success("🟢 Backend: Online")
            else:
                st.warning("🟡 Backend: Degraded")
        except Exception:
            st.error("🔴 Backend: Offline")

        st.divider()

        # Session State Info
        st.subheader("Current Session")

        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())

        st.caption(f"Session ID: {st.session_state.session_id}")

        if "conversation_id" in st.session_state and st.session_state.conversation_id:
            st.caption(f"Conversation ID: {st.session_state.conversation_id}")
            if st.button("Clear Current Conversation", use_container_width=True):
                st.session_state.conversation_id = None
                if "chat_history" in st.session_state:
                    st.session_state.chat_history = []
                st.rerun()
        else:
            st.caption("No active conversation.")

        st.divider()

        st.subheader("Integrations")
        try:
            integrations = api_client.get_integrations()
            if integrations:
                for integration in integrations:
                    # e.g., github
                    name = integration.get("name", "Unknown").capitalize()
                    st.caption(f"✅ {name} connected")
            else:
                st.caption("No active integrations.")
        except Exception:
            st.caption("⚠️ Could not fetch integrations.")

        st.divider()
        st.markdown("[View Source](https://github.com/)")
