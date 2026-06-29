import streamlit as st

st.set_page_config(
    page_title="Enterprise AI Operations",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

from components.sidebar import render_sidebar

# Initialize Session State Variables
if "session_id" not in st.session_state:
    import uuid

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

render_sidebar()

st.title("Autonomous Enterprise Manager")
st.markdown("""
### Welcome to the AI Operations Console

This internal dashboard allows you to:
- **Chat**: Interact with the AI Agent and monitor execution traces.
- **Documents**: Upload and index enterprise PDFs into the vector store.
- **GitHub**: Index GitHub repositories, code, issues, and PRs.
- **Conversations**: Review the PostgreSQL-backed enterprise memory.
- **Metrics**: Analyze performance and observability data.

Please select a tool from the sidebar to begin.
""")
