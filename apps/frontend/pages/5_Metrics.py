import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.metrics import render_metrics

render_sidebar()

st.title("System Metrics & Observability")
st.markdown("Analyze agent performance and node execution durations.")

if "metrics" in st.session_state and st.session_state.metrics:
    st.subheader("Latest Execution Metrics")
    render_metrics(st.session_state.metrics)
else:
    st.info(
        "No metrics available for the current session. Run a chat query to generate metrics."
    )

st.divider()

if "trace" in st.session_state and st.session_state.trace:
    st.subheader("Latest Execution Trace Duration")
    trace = st.session_state.trace
    df = pd.DataFrame(trace)

    if not df.empty and "node" in df.columns and "duration_ms" in df.columns:
        st.bar_chart(df.set_index("node")["duration_ms"])

        st.dataframe(
            df.rename(columns={"node": "Node", "duration_ms": "Duration (ms)"}),
            use_container_width=True,
        )
else:
    st.info("No execution trace available.")
