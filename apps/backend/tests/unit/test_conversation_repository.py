import uuid
from app.repositories.conversation_repository import ConversationRepository
from app.models.memory import Conversation


def test_conversation_repository(mocker):
    mock_db = mocker.MagicMock()
    repo = ConversationRepository(mock_db)

    # Test create_conversation
    session_id = str(uuid.uuid4())
    repo.create_conversation(session_id)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    # Test get_conversation
    conv_id = str(uuid.uuid4())
    mock_conv = Conversation(id=uuid.UUID(conv_id))

    mock_query = mocker.MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_conv

    result = repo.get_conversation(conv_id)
    assert result == mock_conv

    # Test list_conversations
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = [mock_conv]
    results = repo.list_conversations(session_id)
    assert len(results) == 1
    assert results[0] == mock_conv

    # Test delete_conversation
    repo.delete_conversation(conv_id)
    mock_db.delete.assert_called_once_with(mock_conv)
    assert mock_db.commit.call_count == 2
