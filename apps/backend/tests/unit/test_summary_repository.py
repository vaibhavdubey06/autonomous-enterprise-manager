import pytest
import uuid
from app.repositories.summary_repository import SummaryRepository
from app.models.memory import ConversationSummary

def test_summary_repository(mocker):
    mock_db = mocker.MagicMock()
    repo = SummaryRepository(mock_db)
    
    # Test get_latest_summary
    uid = uuid.uuid4()
    mock_summary = ConversationSummary(conversation_id=uid, summary="test")
    mock_query = mocker.MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.first.return_value = mock_summary
    
    result = repo.get_latest_summary(str(uid))
    assert result == mock_summary
    
    # Test create_summary
    repo.create_summary(str(uid), "new summary")
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
