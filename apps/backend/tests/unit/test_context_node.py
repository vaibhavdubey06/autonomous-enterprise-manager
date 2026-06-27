import pytest
from app.graph.nodes.context_node import context_node
from app.graph.state import GraphState

def test_context_node(mocker):
    # Mock build_merged_context
    mock_build = mocker.patch("app.graph.nodes.context_node.build_merged_context")
    mock_build.return_value = ("merged context", ["reranked chunk"], [{"source": "test"}])
    
    state: GraphState = {
        "question": "test question",
        "session_id": "test",
        "conversation_id": "test",
        "enterprise_context": [{"text": "chunk 1", "score": 0.9}],
        "memory_context": "memory string",
        "tool_results": [],
        "execution_trace": [],
        "metrics": {}
    }
    
    result = context_node(state)
    
    assert "merged_context" in result
    assert result["merged_context"] == "merged context"
    assert "context_texts" in result
    assert len(result["context_texts"]) == 1
    assert "sources" in result
    assert len(result["sources"]) == 1
    assert "context_ms" in result["metrics"]
    
    # Test error
    mock_build.side_effect = Exception("Test error")
    result = context_node(state)
    assert result["merged_context"] == ""
