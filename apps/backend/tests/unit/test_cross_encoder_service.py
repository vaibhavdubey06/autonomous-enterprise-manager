import pytest
from fastapi import HTTPException
from app.services.reranking.cross_encoder_service import CrossEncoderService

def test_cross_encoder_service(mocker):
    # Mock CrossEncoder
    mock_ce_class = mocker.patch("app.services.reranking.cross_encoder_service.CrossEncoder")
    mock_instance = mocker.MagicMock()
    mock_ce_class.return_value = mock_instance
    
    mock_instance.predict.return_value = [0.1, 0.9]
    
    service = CrossEncoderService()
    
    # Test rerank
    chunks = [
        {"text": "low score chunk"},
        {"text": "high score chunk"}
    ]
    
    results = service.rerank_chunks("query", chunks, 1)
    
    assert len(results) == 1
    assert results[0]["text"] == "high score chunk"
    assert results[0]["rerank_score"] == 0.9
    
    # Test empty chunks
    results = service.rerank_chunks("query", [], 1)
    assert results == []
    
    # Test exception during init
    mock_ce_class.side_effect = Exception("init error")
    with pytest.raises(RuntimeError):
        CrossEncoderService()
        
    # Test exception during prediction
    mock_ce_class.side_effect = None
    service = CrossEncoderService()
    mock_instance.predict.side_effect = Exception("prediction error")
    with pytest.raises(HTTPException) as excinfo:
        service.rerank_chunks("query", [{"text": "chunk"}], 1)
    assert excinfo.value.status_code == 500

