import pytest

@pytest.mark.asyncio
async def test_graph_execution(client, db_session, mocker):
    payload = {
        "question": "What is the meaning of life?",
        "session_id": "test_session_lg"
    }
    
    response = client.post("/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Verify Supervisor observability metrics
    assert "metrics" in data
    metrics = data["metrics"]
    
    assert "total_time_ms" in metrics
    assert "selected_agents" in metrics
    assert "completed_tasks" in metrics
    
    # At least the Knowledge Agent should have been selected
    assert "Knowledge Agent" in metrics["selected_agents"]
    
    # We should have at least one completed task
    assert len(metrics["completed_tasks"]) >= 1
