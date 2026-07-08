import uuid
from app.repositories.message_repository import MessageRepository
from app.models.memory import Message


def test_message_repository(mocker):
    mock_db = mocker.MagicMock()
    repo = MessageRepository(mock_db)

    # Test add_message
    conv_id = str(uuid.uuid4())
    repo.add_message(conv_id, "user", "hello")
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    # Test get_recent_messages
    mock_msg = Message(conversation_id=uuid.UUID(conv_id), role="user", content="hello")
    mock_query = mocker.MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [mock_msg]

    results = repo.get_recent_messages(conv_id, 10)
    assert len(results) == 1
    assert results[0] == mock_msg

    # Test get_all_messages
    results = repo.get_all_messages(conv_id)
    assert len(results) == 1
    assert results[0] == mock_msg
