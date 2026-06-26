import streamlit as st
import pandas as pd

def render_trace(execution_trace: list):
    if not execution_trace:
        return
        
    with st.expander("⏱️ Execution Trace", expanded=False):
        # Convert trace directly to DataFrame
        df = pd.DataFrame(execution_trace)
        if "node" in df.columns and "duration_ms" in df.columns:
            # We can show a simple table
            df = df.rename(columns={"node": "Node", "duration_ms": "Duration (ms)"})
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Simple timeline visualization
            st.caption("Timeline Visualization")
            for item in execution_trace:
                node = item.get("node", "Unknown")
                dur = item.get("duration_ms", 0)
                st.progress(min(dur / 5000.0, 1.0), text=f"{node} ({dur:.2f} ms)")
        else:
            st.json(execution_trace)
