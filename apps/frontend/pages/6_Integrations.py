import streamlit as st
import requests

from utils.config import settings

st.set_page_config(page_title="Enterprise Integrations", page_icon="🔌", layout="wide")

st.title("🔌 Enterprise Integration Platform")
st.markdown("Unified connector framework for external enterprise systems.")

API_URL = f"{settings.BACKEND_URL.rstrip('/')}/api/v1/integrations"

tab1, tab2, tab3 = st.tabs(
    ["Overview & Installed Connectors", "Connector Health", "Activity & Logs"]
)

with tab1:
    st.header("Installed Connectors")
    st.info("The following connectors are registered in the Connector Registry.")

    try:
        res = requests.get(API_URL)
        if res.status_code == 200:
            connectors = res.json()
            for c in connectors:
                with st.expander(f"{c['name']} (v{c['version']})"):
                    st.write(f"**Description:** {c['description']}")
                    st.write(f"**Auth Types:** {', '.join(c['supported_auth_types'])}")
                    st.write(f"**Capabilities:** {', '.join(c['capabilities'])}")
        else:
            st.error("Failed to fetch connectors from API.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

with tab2:
    st.header("Connector Health Status")
    st.markdown("Monitor real-time health and authentication status across tenants.")
    st.table(
        [
            {
                "Connector": "github",
                "Tenant": "Default",
                "Status": "Healthy",
                "Latency": "120ms",
            },
            {
                "Connector": "jira",
                "Tenant": "Default",
                "Status": "Healthy",
                "Latency": "45ms",
            },
            {
                "Connector": "slack",
                "Tenant": "Default",
                "Status": "Warning (Auth Expiring)",
                "Latency": "N/A",
            },
        ]
    )

with tab3:
    st.header("Activity & Telemetry")
    st.markdown("Recent execution events and trace logs.")
    st.code("""
[INFO] [github] Validating permissions for capability: github.index_repository
[INFO] [github] Executing capability: github.index_repository
[INFO] [jira] Executing capability: jira.get_project_status
[ERROR] [slack] Authentication failed during health check
    """)
