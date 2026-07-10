import streamlit as st
import requests

from utils.config import settings

API_URL = f"{settings.BACKEND_URL.rstrip('/')}/api/v1/operations"

st.set_page_config(page_title="Enterprise Operations Platform", layout="wide")

st.title("Enterprise Operations Platform (EOP)")
st.markdown("Complete operational visibility across all enterprise AI subsystems.")

tabs = st.tabs(
    [
        "Overview",
        "Health",
        "Traces",
        "Metrics",
        "Cost",
        "Alerts",
        "Analytics",
        "System",
        "Logs",
    ]
)

with tabs[0]:
    st.subheader("Operations Overview")
    st.markdown(
        "Select a tab above to explore telemetry, traces, metrics, cost, alerts, and analytics."
    )

with tabs[1]:
    st.subheader("Subsystem Health")
    if st.button("Refresh Health", key="health"):
        try:
            res = requests.get(f"{API_URL}/health")
            if res.status_code == 200:
                data = res.json()
                for subsystem, status in data.items():
                    color = (
                        "🟢"
                        if status == "Healthy"
                        else "🟡" if status in ["Warning", "Busy"] else "🔴"
                    )
                    st.markdown(f"{color} **{subsystem}**: {status}")
        except Exception as e:
            st.error(f"Error: {e}")

with tabs[2]:
    st.subheader("Distributed Traces")
    if st.button("Refresh Traces", key="traces"):
        try:
            res = requests.get(f"{API_URL}/traces")
            if res.status_code == 200:
                data = res.json()
                if not data:
                    st.info("No traces recorded yet.")
                for trace_id, spans in data.items():
                    with st.expander(f"Trace: {trace_id} ({len(spans)} spans)"):
                        for span in spans:
                            st.json(span)
        except Exception as e:
            st.error(f"Error: {e}")

with tabs[3]:
    st.subheader("Metrics Dashboard")
    if st.button("Refresh Metrics", key="metrics"):
        try:
            res = requests.get(f"{API_URL}/metrics")
            if res.status_code == 200:
                st.json(res.json())
        except Exception as e:
            st.error(f"Error: {e}")

with tabs[4]:
    st.subheader("Cost & Token Usage")
    if st.button("Refresh Cost", key="cost"):
        try:
            res = requests.get(f"{API_URL}/cost")
            if res.status_code == 200:
                data = res.json()
                st.metric("Total Cost (USD)", f"${data.get('total_cost_usd', 0):.4f}")
                st.metric("Total Tokens", f"{data.get('total_tokens', 0):,}")
                st.json(data)
        except Exception as e:
            st.error(f"Error: {e}")

with tabs[5]:
    st.subheader("Active Alerts")
    if st.button("Refresh Alerts", key="alerts"):
        try:
            res = requests.get(f"{API_URL}/alerts")
            if res.status_code == 200:
                data = res.json()
                if not data:
                    st.success("No active alerts.")
                for alert in data:
                    severity = alert.get("severity", "INFO")
                    icon = "🔴" if severity == "CRITICAL" else "🟡"
                    st.warning(f"{icon} [{severity}] {alert.get('message')}")
        except Exception as e:
            st.error(f"Error: {e}")

with tabs[6]:
    st.subheader("Operational Analytics")
    if st.button("Refresh Analytics", key="analytics"):
        try:
            res = requests.get(f"{API_URL}/analytics")
            if res.status_code == 200:
                st.json(res.json())
        except Exception as e:
            st.error(f"Error: {e}")

with tabs[7]:
    st.subheader("System Resources")
    if st.button("Refresh System", key="system"):
        try:
            res = requests.get(f"{API_URL}/system")
            if res.status_code == 200:
                data = res.json()
                c1, c2, c3 = st.columns(3)
                c1.metric("CPU", f"{data.get('cpu_percent', 0)}%")
                c2.metric("RAM", f"{data.get('ram_percent', 0)}%")
                c3.metric("Disk", f"{data.get('disk_percent', 0)}%")
        except Exception as e:
            st.error(f"Error: {e}")

with tabs[8]:
    st.subheader("Structured Logs")
    if st.button("Refresh Logs", key="logs"):
        try:
            res = requests.get(f"{API_URL}/logs")
            if res.status_code == 200:
                data = res.json()
                if not data:
                    st.info("No logs recorded yet.")
                for log in data[-50:]:  # Show last 50
                    st.markdown(
                        f"`{log.get('timestamp')}` | **{log.get('component')}** | `{log.get('severity')}` | {log.get('message')}"
                    )
        except Exception as e:
            st.error(f"Error: {e}")
