import pytest
from app.core.database import get_db


def test_get_db(mocker):
    # This is a simple test to cover the get_db generator
    mock_session = mocker.patch("app.core.database.SessionLocal")
    mock_instance = mocker.MagicMock()
    mock_session.return_value = mock_instance

    gen = get_db()
    db = next(gen)

    assert db == mock_instance

    with pytest.raises(StopIteration):
        next(gen)

    mock_instance.close.assert_called_once()
