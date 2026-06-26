import streamlit as st
from services.api_client import api_client
from components.sidebar import render_sidebar
from components.conversation import render_conversation_detail

render_sidebar()

st.title("Conversations Memory")
st.markdown("Browse and manage PostgreSQL-backed Enterprise Memory.")

try:
    sessions = api_client.get_sessions()
except Exception as e:
    st.error(f"Could not load sessions: {str(e)}")
    sessions = []

if not sessions:
    st.info("No sessions found.")
    st.stop()

session_options = {s["id"]: f"Session {s['id'][:8]}... (Created: {s['created_at']})" for s in sessions}
selected_session_id = st.selectbox("Select Session", options=list(session_options.keys()), format_func=lambda x: session_options[x])

if selected_session_id:
    try:
        conversations = api_client.get_conversations(selected_session_id)
    except Exception as e:
        st.error(f"Could not load conversations: {str(e)}")
        conversations = []
        
    if not conversations:
        st.info("No conversations found in this session.")
    else:
        convo_options = {c["id"]: f"{c.get('title', 'Untitled')} ({c['created_at']})" for c in conversations}
        selected_convo_id = st.selectbox("Select Conversation", options=list(convo_options.keys()), format_func=lambda x: convo_options[x])
        
        if selected_convo_id:
            try:
                convo_detail = api_client.get_conversation(selected_convo_id)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    render_conversation_detail(convo_detail)
                
                with col2:
                    st.subheader("Actions")
                    if st.button("Continue this Conversation", use_container_width=True):
                        st.session_state.session_id = selected_session_id
                        st.session_state.conversation_id = selected_convo_id
                        # Clear history to force reload from backend on next chat or we could pre-fill it here
                        st.session_state.chat_history = []
                        for msg in convo_detail.get("messages", []):
                            st.session_state.chat_history.append({
                                "role": msg.get("role", "user"),
                                "content": msg.get("content", "")
                            })
                        st.success("Conversation loaded into current session! Switch to Chat page.")
                        
                    if st.button("Delete Conversation", type="primary", use_container_width=True):
                        try:
                            api_client.delete_conversation(selected_convo_id)
                            st.success("Conversation deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {str(e)}")
                            
            except Exception as e:
                st.error(f"Could not load conversation details: {str(e)}")
