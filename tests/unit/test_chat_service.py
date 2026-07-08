from unittest.mock import MagicMock
from app.services.chat_service import ChatService


def test_chat_service_chat(mocker):
    # Mock dependencies
    mock_llm = MagicMock()
    mock_llm.generate_answer.return_value = "Mocked answer"

    mock_reranker = MagicMock()
    mock_reranker.rerank_chunks.return_value = [
        {
            "text": "mock context 1",
            "source": "conversation",
            "rerank_score": 0.9,
            "conversation_id": "conv1",
            "message_id": "msg1",
            "role": "user",
            "timestamp": "now",
        },
        {
            "text": "mock context 2",
            "source": "github",
            "rerank_score": 0.8,
            "repository": "test/repo",
            "branch": "main",
            "path": "test.txt",
            "url": "http",
        },
        {
            "text": "mock context 3",
            "source": "document",
            "rerank_score": 0.7,
            "document": "test.pdf",
            "page": 1,
            "chunk": 0,
        },
    ]

    mock_memory = MagicMock()
    mock_memory.get_or_create_session.return_value = "test_session"
    mock_memory.get_or_create_conversation.return_value = "test_conversation"
    mock_memory.build_memory_context.return_value = "Previous context"
    mock_memory.retrieve_semantic_memory.return_value = [
        {"text": "semantic context", "source": "conversation"}
    ]

    mocker.patch(
        "app.services.chat_service.search",
        return_value=[{"text": "doc context", "source": "document"}],
    )

    service = ChatService(
        llm_service=mock_llm, reranker_service=mock_reranker, memory_service=mock_memory
    )

    result = service.chat("What is AI?", "test_session", "test_conversation")

    assert result["answer"] == "Mocked answer"
    assert result["session_id"] == "test_session"
    assert result["conversation_id"] == "test_conversation"
    assert len(result["sources"]) == 3

    mock_llm.generate_answer.assert_called_once()
    mock_memory.save_message.assert_any_call("test_conversation", "user", "What is AI?")
    mock_memory.save_message.assert_any_call(
        "test_conversation", "assistant", "Mocked answer"
    )
