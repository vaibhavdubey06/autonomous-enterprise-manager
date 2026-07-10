from app.graph.nodes.retrieval_node import make_retrieval_node
from app.graph.state import GraphState


def test_retrieval_node(mocker):
    # Mock engine.retrieve
    mock_retrieve = mocker.patch("app.graph.nodes.retrieval_node.engine.retrieve")
    mock_chunk = mocker.MagicMock()
    mock_chunk.score = 0.9
    mock_chunk.text = "chunk 1"
    mock_chunk.metadata = {"document": "doc1", "page": 1, "chunk": 0}
    mock_chunk.source = "source1"
    mock_chunk.repository = "repo1"
    mock_chunk.citation = "cit1"

    mock_result = mocker.MagicMock()
    mock_result.chunks = [mock_chunk]
    mock_result.strategy_used = "mock"
    mock_retrieve.return_value = mock_result

    mock_services = mocker.MagicMock()

    node = make_retrieval_node(mock_services)
    state: GraphState = {
        "question": "test question",
        "session_id": "test",
        "conversation_id": "test",
        "enterprise_context": [],
        "execution_trace": [],
        "metrics": {},
    }

    result = node(state)

    assert "enterprise_context" in result
    assert len(result["enterprise_context"]) == 1
    assert result["enterprise_context"][0]["text"] == "chunk 1"
    assert "retrieval_ms" in result["metrics"]

    # Test error
    mock_retrieve.side_effect = Exception("Test error")
    result = node(state)
    assert len(result["enterprise_context"]) == 0
