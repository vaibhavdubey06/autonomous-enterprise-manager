import pytest
from app.graph.nodes.retrieval_node import make_retrieval_node
from app.graph.state import GraphState

def test_retrieval_node(mocker):
    # Mock search
    mock_search = mocker.patch("app.graph.nodes.retrieval_node.search")
    mock_search.return_value = [{"text": "chunk 1", "score": 0.9}]
    
    mock_services = mocker.MagicMock()
    mock_services.cross_encoder_service.rerank_chunks.return_value = [{"text": "chunk 1", "score": 0.9}]
    
    node = make_retrieval_node(mock_services)
    state: GraphState = {
        "question": "test question",
        "session_id": "test",
        "conversation_id": "test",
        "enterprise_context": [],
        "execution_trace": [],
        "metrics": {}
    }
    
    result = node(state)
    
    assert "enterprise_context" in result
    assert len(result["enterprise_context"]) == 1
    assert result["enterprise_context"][0]["text"] == "chunk 1"
    assert "retrieval_ms" in result["metrics"]
    
    # Test error
    mock_search.side_effect = Exception("Test error")
    result = node(state)
    assert len(result["enterprise_context"]) == 0
