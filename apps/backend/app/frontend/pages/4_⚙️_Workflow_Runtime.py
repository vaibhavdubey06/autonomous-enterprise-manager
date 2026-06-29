import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(
    page_title="Workflow Runtime Dashboard", page_icon="⚙️", layout="wide"
)

st.title("⚙️ Enterprise Workflow Runtime")
st.markdown("Monitor and control Autonomous Enterprise Workflows.")

API_BASE = (
    f"{os.getenv('BACKEND_URL', 'http://backend:8000').rstrip('/')}/api/v1/workflows"
)


def fetch_workflows():
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            return response.json()
        st.error(f"Failed to fetch workflows: {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
    return []


workflows = fetch_workflows()

if not workflows:
    st.info("No workflows found. Run the CTO Agent to generate a workflow.")
else:
    df = pd.DataFrame(workflows)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values(by="created_at", ascending=False)

    st.subheader("Active Workflows")

    # Overview Table
    st.dataframe(
        df[["workflow_id", "goal", "owner_agent", "status", "created_at"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Workflow Details")
    selected_workflow = st.selectbox(
        "Select a workflow to inspect", options=df["workflow_id"].tolist()
    )

    if selected_workflow:
        # Fetch detailed workflow with tasks
        detail_res = requests.get(f"{API_BASE}/{selected_workflow}")
        if detail_res.status_code == 200:
            wf = detail_res.json()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Status", wf["status"])
            col2.metric("Owner Agent", wf.get("owner_agent", "System"))
            col3.metric("Tasks Count", len(wf.get("tasks", [])))
            col4.metric("Priority", wf.get("priority", 0))

            st.markdown(f"**Goal:** {wf['goal']}")
            if wf.get("description"):
                st.markdown(f"**Description:** {wf['description']}")

            st.divider()

            st.subheader("Task Execution DAG")
            tasks = wf.get("tasks", [])
            if tasks:
                for task in tasks:
                    status_emoji = {
                        "Pending": "⏳",
                        "Running": "🔄",
                        "Completed": "✅",
                        "Failed": "❌",
                        "Cancelled": "🛑",
                    }.get(task["status"], "❓")

                    with st.expander(
                        f"{status_emoji} Task: {task.get('name', task['task_id'])} ({task['status']})"
                    ):
                        st.json(
                            {
                                "Task ID": task["task_id"],
                                "Type": task["task_type"],
                                "Capability": task.get("required_capability"),
                                "Dependencies": task.get("dependencies", []),
                                "Inputs": task.get("inputs", {}),
                                "Outputs": task.get("outputs", {}),
                            }
                        )
            else:
                st.info("No tasks associated with this workflow.")

            # Actions
            st.divider()
            st.subheader("Controls")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("▶️ Execute Workflow"):
                    res = requests.post(f"{API_BASE}/{selected_workflow}/execute")
                    if res.status_code == 200:
                        st.success("Execution started!")
                    else:
                        st.error(f"Error: {res.text}")
            with c2:
                if st.button("⏸️ Pause Workflow"):
                    res = requests.post(f"{API_BASE}/{selected_workflow}/pause")
                    st.toast("Workflow paused")
            with c3:
                if st.button("🛑 Cancel Workflow"):
                    res = requests.post(f"{API_BASE}/{selected_workflow}/cancel")
                    st.toast("Workflow cancelled")
