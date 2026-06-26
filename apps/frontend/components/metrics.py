import streamlit as st
import pandas as pd

def render_metrics(metrics: dict):
    if not metrics:
        return
        
    with st.expander("📊 Execution Metrics", expanded=False):
        # We can display key-value pairs as streamlit metrics in columns
        keys = list(metrics.keys())
        # create rows of 3 columns
        for i in range(0, len(keys), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(keys):
                    key = keys[i+j]
                    val = metrics[key]
                    
                    # Format value if it's a float
                    if isinstance(val, float):
                        val_str = f"{val:.2f}"
                        if "time" in key.lower() or "duration" in key.lower():
                            val_str += " s"
                    else:
                        val_str = str(val)
                        
                    col.metric(label=key.replace("_", " ").title(), value=val_str)
