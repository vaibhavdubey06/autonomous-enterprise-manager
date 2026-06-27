import pytest
from app.services.reranking.cross_encoder_service import CrossEncoderService
from app.core.config import settings

def test_cross_encoder_service(mocker):
    # Mock the cross encoder model
    mock_model = mocker.MagicMock()
    mock_model.predict.return_value = [0.9, 0.1, 0.5]
    
    mocker.patch("app.services.reranking.cross_encoder_service.CrossEncoder", return_value=mock_model)


    service = CrossEncoderService()
    
    chunks = [
        {"text": "chunk 1", "source": "test"},
        {"text": "chunk 2", "source": "test"},
        {"text": "chunk 3", "source": "test"}
    ]
    
    results = service.rerank_chunks("query", chunks, top_k=2)
    
    assert len(results) == 2
    assert results[0]["text"] == "chunk 1"
    assert results[0]["rerank_score"] == 0.9
    assert results[1]["text"] == "chunk 3"
    assert results[1]["rerank_score"] == 0.5
