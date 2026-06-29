import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.collaboration.session.collaboration_session import SessionPhase
from app.collaboration.session.session_repository import SessionRepository
from app.collaboration.session.session_state_machine import SessionStateMachine

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_session_state_machine_valid():
    assert (
        SessionStateMachine.can_transition(SessionPhase.CREATED, SessionPhase.PLANNING)
        is True
    )
    assert (
        SessionStateMachine.can_transition(
            SessionPhase.PLANNING, SessionPhase.TEAM_FORMATION
        )
        is True
    )


def test_session_state_machine_invalid():
    assert (
        SessionStateMachine.can_transition(SessionPhase.CREATED, SessionPhase.COMPLETED)
        is False
    )
    with pytest.raises(ValueError):
        SessionStateMachine.validate_transition(
            SessionPhase.CREATED, SessionPhase.COMPLETED
        )


def test_session_repository(db):
    repo = SessionRepository(db)

    # 1. Create
    session = repo.create_session("sess1", "Test objective")
    assert session.session_id == "sess1"
    assert session.current_phase == SessionPhase.CREATED

    # 2. Update phase
    session = repo.update_phase("sess1", SessionPhase.PLANNING)
    assert session.current_phase == SessionPhase.PLANNING

    # 3. Invalid phase update
    with pytest.raises(ValueError):
        repo.update_phase("sess1", SessionPhase.COMPLETED)

    # 4. Update attributes
    session = repo.update_session(
        "sess1", {"leader": "CTO", "participants": ["CTO", "CFO"]}
    )
    assert session.leader == "CTO"
    assert "CFO" in session.participants
