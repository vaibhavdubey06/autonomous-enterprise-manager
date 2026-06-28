import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000/api/v1/collaboration"

st.set_page_config(page_title="Enterprise Collaboration Runtime", layout="wide")

st.title("Enterprise Collaboration Runtime (ECR)")
st.markdown("Monitor and interact with executive agent collaboration sessions.")

# Helper to fetch active sessions (Mocked for UI demo since we don't have a GET /sessions endpoint yet)
st.subheader("Active Collaboration Sessions")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Create New Session")
    objective = st.text_area("Objective")
    workflow_id = st.text_input("Associated Workflow ID (Optional)")
    if st.button("Initialize Session"):
        try:
            res = requests.post(f"{API_URL}/session", json={
                "objective": objective,
                "workflow_id": workflow_id if workflow_id else None
            })
            if res.status_code == 200:
                st.success(f"Session created: {res.json().get('session_id')}")
            else:
                st.error(f"Error: {res.text}")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")

with col2:
    st.markdown("### Retrieve Session details")
    session_id = st.text_input("Session ID")
    if st.button("Refresh"):
        try:
            res = requests.get(f"{API_URL}/session/{session_id}")
            if res.status_code == 200:
                data = res.json()
                st.json(data)
            else:
                st.warning("Session not found")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")

st.divider()

st.subheader("Collaboration Actions")
act1, act2, act3 = st.columns(3)

with act1:
    st.markdown("### Start Negotiation")
    neg_topic = st.text_input("Negotiation Topic")
    neg_proposer = st.text_input("Proposer Agent")
    neg_content = st.text_area("Proposal Content")
    if st.button("Submit Proposal"):
        res = requests.post(f"{API_URL}/negotiate?session_id={session_id}", json={
            "topic": neg_topic,
            "proposer": neg_proposer,
            "content": neg_content
        })
        st.write(res.json() if res.status_code == 200 else res.text)

with act2:
    st.markdown("### Cast Consensus Vote")
    con_topic = st.text_input("Consensus Topic")
    con_agent = st.text_input("Agent ID")
    con_opt = st.text_input("Option")
    if st.button("Vote"):
        res = requests.post(f"{API_URL}/consensus?session_id={session_id}", json={
            "topic": con_topic,
            "agent_id": con_agent,
            "option": con_opt
        })
        st.write(res.json() if res.status_code == 200 else res.text)

with act3:
    st.markdown("### Raise Conflict")
    cf_topic = st.text_input("Conflict Topic")
    cf_parts = st.text_input("Participants (comma separated)")
    cf_sev = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
    if st.button("Raise Conflict"):
        res = requests.post(f"{API_URL}/conflict?session_id={session_id}", json={
            "topic": cf_topic,
            "participants": [p.strip() for p in cf_parts.split(",")],
            "severity": cf_sev
        })
        st.write(res.json() if res.status_code == 200 else res.text)
