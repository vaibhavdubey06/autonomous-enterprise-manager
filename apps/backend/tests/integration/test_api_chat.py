def test_chat_endpoint(client, mocker):
    mocker.patch(
        "app.api.v1.chat.ChatService.chat",
        return_value={
            "session_id": "test_session",
            "conversation_id": "test_conversation",
            "answer": "This is a chat answer",
            "sources": [],
        },
    )

    payload = {"question": "What is AI?", "session_id": "test_session"}

    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"] == "This is a chat answer"
    assert data["session_id"] == "test_session"
