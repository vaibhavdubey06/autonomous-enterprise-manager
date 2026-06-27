import pytest
from app.services.vectorstore.qdrant_service import store_chunks, search, create_collection

def test_store_chunks(mocker):
    mock_get_client = mocker.patch("app.services.vectorstore.qdrant_service.get_client")
    mock_client = mocker.MagicMock()
    mock_get_client.return_value = mock_client
    
    chunks = [{"text": "chunk 1", "page": 1}]
    embeddings = [[0.1, 0.2]]
    
    store_chunks(chunks, embeddings, "test.pdf")
    
    mock_client.upsert.assert_called_once()

def test_search(mocker):
    mock_get_client = mocker.patch("app.services.vectorstore.qdrant_service.get_client")
    mock_client = mocker.MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_collection = mocker.MagicMock()
    mock_collection.name = "documents"
    mock_client.get_collections.return_value = mocker.MagicMock(collections=[mock_collection])
    
    mock_embed = mocker.patch("app.services.embeddings.embedding_service.embed_text")
    mock_embed.return_value = [0.1, 0.2]
    
    mock_scored_point = mocker.MagicMock()
    mock_scored_point.payload = {"text": "chunk 1", "document": "test.pdf", "source": "document"}
    mock_scored_point.score = 0.9
    mock_client.query_points.return_value = mocker.MagicMock(points=[mock_scored_point])
    
    results = search("query", limit=1)
    
    assert len(results) == 1
    assert results[0]["text"] == "chunk 1"
    assert results[0]["document"] == "test.pdf"
    
    mock_client.query_points.assert_called_once()

def test_create_collection(mocker):
    mock_get_client = mocker.patch("app.services.vectorstore.qdrant_service.get_client")
    mock_client = mocker.MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_client.get_collections.return_value = mocker.MagicMock(collections=[])
    
    create_collection()
    
    mock_client.create_collection.assert_called_once()

