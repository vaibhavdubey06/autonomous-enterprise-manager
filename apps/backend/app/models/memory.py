import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="session", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("Session", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    summaries = relationship("ConversationSummary", back_populates="conversation", cascade="all, delete-orphan")


class KnowledgeItem(Base):
    """
    Generic base abstraction for all enterprise knowledge artifacts.
    """
    __abstract__ = True


class Message(KnowledgeItem):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)
    role = Column(String, index=True)  # "user" or "assistant"
    content = Column(Text)
    importance = Column(Float, default=0.5)
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="summaries")


from sqlalchemy import Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB
import json

class MemoryObject(KnowledgeItem):
    __tablename__ = "memory_objects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    user_id = Column(String, index=True)
    memory_type = Column(String, index=True)
    title = Column(String)
    content = Column(Text)
    importance = Column(Float, default=0.5)
    confidence = Column(Float, default=0.5)
    memory_status = Column(String, default="NEW")
    
    # Provenance
    source = Column(String)
    source_message_id = Column(UUID(as_uuid=True), nullable=True)
    source_conversation_id = Column(UUID(as_uuid=True), nullable=True)
    source_document_id = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    extracted_by = Column(String, nullable=True)
    extraction_version = Column(String, nullable=True)

    # Retrieval Analytics
    retrieval_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # In SQLite JSONB is not supported directly but for simplicity we can use String and parse it, 
    # but the project specifies PostgreSQL + Qdrant. Since testing uses SQLite, let's use JSON.
    from sqlalchemy import JSON
    metadata_ = Column("metadata", JSON, default=dict)
    tags = Column(JSON, default=list)
    embedding_required = Column(Boolean, default=True)


class MemoryEntity(KnowledgeItem):
    __tablename__ = "memory_entities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Placeholder for future


class MemoryRelationship(KnowledgeItem):
    __tablename__ = "memory_relationships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Placeholder for future
