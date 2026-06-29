def test_memory_endpoints(client, db_session):
    # 1. List sessions for default_user (should be empty initially)
    response = client.get("/sessions?user_id=default_user")
    assert response.status_code == 200
    assert response.json() == []

    # 2. Get non-existent session
    response = client.get("/session/non_existent")
    assert response.status_code == 404

    # 3. Get non-existent conversation
    response = client.get("/conversation/non_existent")
    assert response.status_code == 404

    # The actual creation of sessions/conversations happens via /agent/chat
    # Let's hit the /agent/chat endpoint to create a conversation and session
    payload = {"question": "Hello!", "session_id": "test_session_123"}
    chat_resp = client.post("/agent/chat", json=payload)
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "conversation_id" in chat_data
    conv_id = chat_data["conversation_id"]

    # 4. List sessions again
    response = client.get("/sessions?user_id=default_user")
    assert response.status_code == 200
    assert len(response.json()) > 0

    # 5. Get conversation details
    response = client.get(f"/conversation/{conv_id}")
    assert response.status_code == 200
    conv_data = response.json()
    assert conv_data["id"] == conv_id
    assert len(conv_data["messages"]) >= 2  # At least Human and AI

    # 6. Delete conversation
    response = client.delete(f"/conversation/{conv_id}")
    assert response.status_code == 200

    # 7. Get conversation details (should be 404)
    response = client.get(f"/conversation/{conv_id}")
    assert response.status_code == 404
