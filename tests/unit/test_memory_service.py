from app.services.memory_service import MemoryService


def test_memory_service(mocker):
    # Mock repositories
    mock_session_repo = mocker.MagicMock()
    mock_conv_repo = mocker.MagicMock()
    mock_msg_repo = mocker.MagicMock()
    mock_summary_repo = mocker.MagicMock()
    mock_llm_service = mocker.MagicMock()

    mock_msg = mocker.MagicMock()
    mock_msg.role = "user"
    mock_msg.content = "hello"
    mock_msg.timestamp.isoformat.return_value = "now"
    mock_msg_repo.get_recent_messages.return_value = [mock_msg]

    mock_summary = mocker.MagicMock()
    mock_summary.summary = "A summary"
    mock_summary_repo.get_latest_summary.return_value = mock_summary

    service = MemoryService(
        session_repo=mock_session_repo,
        conversation_repo=mock_conv_repo,
        message_repo=mock_msg_repo,
        summary_repo=mock_summary_repo,
        memory_repo=mocker.MagicMock(),
        llm_service=mock_llm_service,
        extractor=mocker.MagicMock(),
    )

    # Test build_memory_context
    context = service.build_memory_context("conv_1")

    assert "Conversation Summary:" in context
    assert "A summary" in context
    assert "Recent Conversation History:" in context
    assert "User: hello" in context

    # Test retrieve_semantic_memory
    mock_search = mocker.patch("app.services.memory_service.search")
    mock_search.return_value = [
        {"score": 0.9, "text": "semantic context", "role": "user", "timestamp": "now"}
    ]

    results = service.retrieve_semantic_memory("query")
    assert len(results) == 1
    assert results[0]["text"] == "semantic context"
