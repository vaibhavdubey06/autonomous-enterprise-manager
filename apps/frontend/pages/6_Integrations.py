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

                    st.divider()
                    st.markdown("#### Connection Status")

                    connector_name = c["name"].lower()
                    health_res = requests.get(f"{API_URL}/{connector_name}/health")

                    is_connected = False
                    status_str = "unknown"
                    if health_res.status_code == 200:
                        status_str = health_res.json().get("health", "unknown")
                        if status_str != "disconnected":
                            is_connected = True

                    if is_connected:
                        st.success(
                            f"✅ {c['name']} is currently integrated (Status: {status_str})."
                        )
                        if st.button(
                            f"Disconnect {c['name']}",
                            key=f"disconnect_{connector_name}",
                        ):
                            disconnect_url = f"{API_URL}/{connector_name}/disconnect"
                            try:
                                d_res = requests.post(disconnect_url)
                                if d_res.status_code == 200:
                                    st.success("Disconnected successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to disconnect.")
                            except Exception as e:
                                st.error(f"Error disconnecting: {e}")
                    else:
                        with st.form(key=f"form_{connector_name}"):
                            auth_type = st.selectbox(
                                "Auth Type", c["supported_auth_types"]
                            )
                            token = st.text_input(
                                "Access Token / API Key", type="password"
                            )
                            submit = st.form_submit_button("Integrate")
                            if submit:
                                payload = {
                                    "auth_type": auth_type,
                                    "config_data": {"token": token},
                                }
                                connect_url = f"{API_URL}/{connector_name}/connect"
                                try:
                                    conn_res = requests.post(connect_url, json=payload)
                                    if conn_res.status_code == 200:
                                        st.success(
                                            f"Successfully integrated {c['name']}!"
                                        )
                                        st.rerun()
                                    else:
                                        st.error(
                                            f"Failed to integrate: {conn_res.text}"
                                        )
                                except Exception as e:
                                    st.error(f"Error connecting: {e}")
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
