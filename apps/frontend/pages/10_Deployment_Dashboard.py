import os
import subprocess
import time

import psutil
import requests
import streamlit as st

from utils.config import settings

st.set_page_config(page_title="Deployment Dashboard", layout="wide")


def _safe_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _health() -> dict:
    try:
        response = requests.get(f"{settings.BACKEND_URL.rstrip('/')}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {"status": "offline"}


def _metric_columns():
    cpu = psutil.cpu_percent(interval=0.2)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    uptime_hours = int((time.time() - psutil.boot_time()) / 3600)
    return cpu, memory, disk, uptime_hours


st.title("Deployment Dashboard")
st.caption("Operational view of the production release and runtime host.")

health = _health()
cpu, memory, disk, uptime_hours = _metric_columns()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Deployment Version", os.getenv("DEPLOYMENT_VERSION", "1.0.0"))
col2.metric("Git Commit", os.getenv("GIT_COMMIT", _safe_git_commit()))
col3.metric("Build Number", os.getenv("BUILD_NUMBER", "local"))
col4.metric(
    "CloudWatch",
    os.getenv(
        "CLOUDWATCH_STATUS",
        "configured" if os.getenv("CLOUDWATCH_AGENT_CONFIGURED") else "pending",
    ),
)

col5, col6, col7, col8 = st.columns(4)
col5.metric("CPU", f"{cpu:.0f}%")
col6.metric("Memory", f"{memory:.0f}%")
col7.metric("Disk", f"{disk:.0f}%")
col8.metric("Uptime", f"{uptime_hours}h")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Health Status")
    st.write(f"Backend: {health.get('status', 'unknown')}")
    st.json(health)

with right:
    st.subheader("Runtime Context")
    st.write(f"Backend URL: {settings.BACKEND_URL}")
    st.write(f"Hostname: {os.getenv('HOSTNAME', 'unknown')}")
    st.write(f"RSS Memory: {psutil.Process().memory_info().rss / (1024 * 1024):.1f} MB")

st.subheader("Deployment History")
st.info(
    "Release metadata is environment-driven so CI can inject commit, build, and release details without changing application code."
)
