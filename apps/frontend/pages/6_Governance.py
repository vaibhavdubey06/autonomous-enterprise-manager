import streamlit as st
import requests

from utils.config import settings

API_URL = f"{settings.BACKEND_URL.rstrip('/')}/api/v1/governance"

st.set_page_config(page_title="Enterprise Governance Dashboard", layout="wide")

st.title("Enterprise Governance Platform (EGP)")
st.markdown(
    "Monitor policy execution, human approvals, risk assessments, and compliance audits."
)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Pending Approvals")
    if st.button("Refresh Pending"):
        try:
            res = requests.get(f"{API_URL}/pending")
            if res.status_code == 200:
                data = res.json()
                if not data:
                    st.success("No pending approvals.")
                for req in data:
                    st.info(
                        f"Workflow: {req['workflow_id']} | Reason: {req['reason']} | Role: {req['required_role']}"
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Approve", key=f"app_{req['request_id']}"):
                            requests.post(
                                f"{API_URL}/approval/{req['request_id']}/resolve",
                                json={
                                    "approved": True,
                                    "resolved_by": "StreamlitAdmin",
                                },
                            )
                            st.experimental_rerun()
                    with c2:
                        if st.button("Reject", key=f"rej_{req['request_id']}"):
                            requests.post(
                                f"{API_URL}/approval/{req['request_id']}/resolve",
                                json={
                                    "approved": False,
                                    "resolved_by": "StreamlitAdmin",
                                },
                            )
                            st.experimental_rerun()
            else:
                st.error("Failed to fetch pending approvals.")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

with col2:
    st.subheader("Trust Scores")
    if st.button("Refresh Trust Scores"):
        try:
            res = requests.get(f"{API_URL}/trust")
            if res.status_code == 200:
                data = res.json()
                st.json(data)
            else:
                st.error("Failed to fetch trust scores.")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

st.divider()

st.subheader("Audit Timeline")
workflow_id = st.text_input("Workflow ID for Audit Log")
if st.button("Fetch Audit Chain"):
    try:
        res = requests.get(f"{API_URL}/audit/{workflow_id}")
        if res.status_code == 200:
            data = res.json()
            if not data:
                st.info("No audit logs found for this workflow.")
            for log in data:
                st.markdown(f"**{log['timestamp']}** | `{log['event_type']}`")
                st.json(log["details"])
        else:
            st.error("Failed to fetch audit chain.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
