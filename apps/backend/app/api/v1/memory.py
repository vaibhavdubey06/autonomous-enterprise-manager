import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.schemas.memory import (
    SessionSchema,
    ConversationSchema,
    ConversationDetailSchema,
)
from app.repositories.session_repository import SessionRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository

router = APIRouter()
logger = logging.getLogger(__name__)


def get_session_repo(db: DBSession = Depends(get_db)):
    return SessionRepository(db)


def get_conversation_repo(db: DBSession = Depends(get_db)):
    return ConversationRepository(db)


def get_message_repo(db: DBSession = Depends(get_db)):
    return MessageRepository(db)


@router.get("/sessions", response_model=List[SessionSchema])
async def list_sessions(
    user_id: str = "default_user",
    session_repo: SessionRepository = Depends(get_session_repo),
):
    sessions = session_repo.list_sessions(user_id)
    return [
        {
            "id": str(s.id),
            "user_id": s.user_id,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in sessions
    ]


@router.get("/session/{session_id}", response_model=SessionSchema)
async def get_session(
    session_id: str, session_repo: SessionRepository = Depends(get_session_repo)
):
    session = session_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {
        "id": str(session.id),
        "user_id": session.user_id,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


@router.get("/conversations", response_model=List[ConversationSchema])
async def list_conversations(
    session_id: str,
    conversation_repo: ConversationRepository = Depends(get_conversation_repo),
):
    convos = conversation_repo.list_conversations(session_id)
    return [
        {
            "id": str(c.id),
            "session_id": str(c.session_id),
            "title": c.title,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in convos
    ]


@router.get("/conversation/{conversation_id}", response_model=ConversationDetailSchema)
async def get_conversation(
    conversation_id: str,
    conversation_repo: ConversationRepository = Depends(get_conversation_repo),
    message_repo: MessageRepository = Depends(get_message_repo),
):
    conv = conversation_repo.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    messages = message_repo.get_all_messages(conversation_id)
    msg_schemas = [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "importance": m.importance,
            "timestamp": m.timestamp,
        }
        for m in messages
    ]

    return {
        "id": str(conv.id),
        "session_id": str(conv.session_id),
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": msg_schemas,
    }


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    conversation_repo: ConversationRepository = Depends(get_conversation_repo),
):
    success = conversation_repo.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Conversation not found or failed to delete."
        )
    return {"status": "success", "message": "Conversation deleted."}
