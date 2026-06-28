import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.collaboration.messaging.message_models import CollaborationMessage, MessageType
from app.collaboration.messaging.message_bus import MessageBus

# Use an in-memory SQLite database for testing
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

@pytest.mark.asyncio
async def test_message_bus_publish_and_subscribe(db):
    bus = MessageBus(db)
    
    received_all = []
    received_specific = []
    
    def cb_all(msg):
        received_all.append(msg)
        
    def cb_specific(msg):
        received_specific.append(msg)
        
    bus.subscribe("all", cb_all)
    bus.subscribe("agent:CTO", cb_specific)
    
    msg = CollaborationMessage(
        message_id="msg1",
        collaboration_id="collab1",
        sender="System",
        receiver="CTO",
        message_type=MessageType.INFORMATION,
        payload={"text": "Hello CTO"}
    )
    
    await bus.publish(msg)
    
    assert len(received_all) == 1
    assert received_all[0].message_id == "msg1"
    
    assert len(received_specific) == 1
    assert received_specific[0].message_id == "msg1"
    
    # Verify persistence
    saved_msgs = bus.get_messages_for_session("collab1")
    assert len(saved_msgs) == 1
    assert saved_msgs[0].payload == {"text": "Hello CTO"}

@pytest.mark.asyncio
async def test_message_bus_no_receiver(db):
    bus = MessageBus(db)
    received = []
    
    def cb_all(msg):
        received.append(msg)
        
    bus.subscribe("all", cb_all)
    
    msg = CollaborationMessage(
        message_id="msg2",
        collaboration_id="collab2",
        sender="System",
        receiver=None,
        message_type=MessageType.BROADCAST if hasattr(MessageType, 'BROADCAST') else MessageType.INFORMATION,
        payload={"text": "Broadcast"}
    )
    
    await bus.publish(msg)
    
    assert len(received) == 1
    assert received[0].message_id == "msg2"
