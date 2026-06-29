import streamlit as st
from services.api_client import api_client
from components.sidebar import render_sidebar
from components.chat import render_chat_history, render_chat_message
from components.trace import render_trace
from components.metrics import render_metrics
from components.sources import render_sources

render_sidebar()

st.title("Enterprise AI Chat")

# Toggle between Agent (LangGraph) and Legacy
chat_mode = st.radio("Chat Mode", ["LangGraph Agent", "Legacy Chat"], horizontal=True)

# Render Chat History
render_chat_history(st.session_state.chat_history)

# Chat Input
if prompt := st.chat_input("Ask the Enterprise Manager..."):
    # Add user message to state
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    render_chat_message("user", prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Call appropriate endpoint
                if chat_mode == "LangGraph Agent":
                    response = api_client.agent_chat(
                        question=prompt,
                        session_id=st.session_state.session_id,
                        conversation_id=st.session_state.conversation_id,
                    )
                else:
                    response = api_client.chat(
                        question=prompt,
                        session_id=st.session_state.session_id,
                        conversation_id=st.session_state.conversation_id,
                    )

                answer = response.get("answer", "")
                st.markdown(answer)

                st.session_state.chat_history.append(
                    {"role": "assistant", "content": answer}
                )

                # Update Session IDs if returned
                if response.get("conversation_id"):
                    st.session_state.conversation_id = response.get("conversation_id")

                # Update Trace, Metrics, Sources
                st.session_state.trace = response.get("execution_trace", [])
                st.session_state.metrics = response.get("metrics", {})
                st.session_state.sources = response.get("sources", [])

            except Exception as e:
                st.error(f"Error: {str(e)}")

st.divider()

# Observability Panel (always displayed)
st.subheader("Observability & Debugging")
render_trace(st.session_state.trace)
render_metrics(st.session_state.metrics)
render_sources(st.session_state.sources)
