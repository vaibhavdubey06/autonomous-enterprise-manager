import streamlit as st
import requests

from utils.config import settings

st.set_page_config(
    page_title="Enterprise Platform Runtime", page_icon="⚙️", layout="wide"
)

st.title("⚙️ Enterprise Platform Runtime")
st.markdown("Distributed runtime infrastructure and configuration management.")

BACKEND_URL = settings.BACKEND_URL.rstrip("/")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Infrastructure Health", "Cache Framework", "Architecture Manifest"]
)

with tab1:
    st.header("Runtime Environment")
    st.info("The system is currently running in the following profile:")
    st.metric("Profile", "DEVELOPMENT")  # In a real implementation this comes from API

with tab2:
    st.header("Infrastructure Health")
    st.markdown("Health endpoints from the underlying Platform Runtime services.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("API Health")
        try:
            res = requests.get(f"{BACKEND_URL}/health")
            if res.status_code == 200:
                st.success("Healthy")
                st.json(res.json())
            else:
                st.error(f"Error {res.status_code}")
        except Exception:
            st.error("Unreachable")

    with col2:
        st.subheader("Liveness Probe")
        try:
            res = requests.get(f"{BACKEND_URL}/live")
            if res.status_code == 200:
                st.success("Alive")
            else:
                st.error("Dead")
        except Exception:
            st.error("Unreachable")

    with col3:
        st.subheader("Readiness Probe")
        try:
            res = requests.get(f"{BACKEND_URL}/ready")
            if res.status_code == 200:
                st.success("Ready")
            else:
                st.error("Not Ready")
        except Exception:
            st.error("Unreachable")

with tab3:
    st.header("Cache Framework")
    st.markdown("Distributed caching and rate limiting states.")
    st.table(
        [
            {
                "Type": "RateLimiter",
                "Provider": "MemoryCacheProvider",
                "Keys Cached": 52,
            },
            {
                "Type": "SessionStore",
                "Provider": "MemoryCacheProvider",
                "Keys Cached": 12,
            },
        ]
    )

with tab4:
    st.header("Architecture Manifest")
    st.code(
        """
{
  "application": "Autonomous Enterprise Manager",
  "version": "1.1.0",
  "build": "a4b7f32",
  "environment": "development",
  "infrastructure": {
    "kubernetes": false,
    "docker_compose": true,
    "redis": "enabled",
    "postgres_version": "15"
  },
  "deployment_timestamp": "2026-06-28T13:00:00Z"
}
    """,
        language="json",
    )
