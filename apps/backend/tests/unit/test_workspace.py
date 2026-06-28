import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.collaboration.session.collaboration_session import CollaborationSession, SessionPhase
from app.collaboration.workspace.shared_workspace import SharedWorkspace, DecisionRecord
from app.collaboration.workspace.workspace_repository import WorkspaceRepository

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Pre-create a session
    cs = CollaborationSession(
        session_id="session1",
        objective="Test Workspace",
        shared_workspace={}
    )
    session.add(cs)
    session.commit()
    
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_workspace_repository(db):
    repo = WorkspaceRepository(db)
    
    # 1. Get empty workspace
    ws = repo.get_workspace("session1")
    assert len(ws.goals) == 0
    
    # 2. Add goal and save
    ws.add_goal("Optimize costs")
    decision = DecisionRecord(
        decision_id="d1",
        topic="Cloud Provider",
        selected_option="AWS",
        reasoning="Cost effective",
        confidence=0.9,
        timestamp="2023-10-01T12:00:00Z"
    )
    ws.add_decision(decision)
    repo.save_workspace("session1", ws)
    
    # 3. Retrieve and verify
    ws_new = repo.get_workspace("session1")
    assert "Optimize costs" in ws_new.goals
    assert len(ws_new.decisions) == 1
    assert ws_new.decisions[0].decision_id == "d1"
