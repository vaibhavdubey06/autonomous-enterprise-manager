import pytest

def test_execution_trace(client, db_session):
    payload = {
        "question": "Hello trace",
        "session_id": "test_session_trace"
    }
    
    response = client.post("/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "execution_trace" in data
    trace = data["execution_trace"]
    assert isinstance(trace, list)
    
    if len(trace) > 0:
        first_trace = trace[0]
        assert "node" in first_trace
        assert "duration_ms" in first_trace
        assert isinstance(first_trace["duration_ms"], (int, float))
    
    assert "metrics" in data
    metrics = data["metrics"]
    assert "total_time_ms" in metrics
