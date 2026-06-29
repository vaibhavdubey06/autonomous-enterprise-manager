from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.collaboration.schemas.collaboration import (
    CollaborationSessionCreate,
    CollaborationSessionResponse,
    DelegateRequest,
    NegotiateRequest,
    ConsensusRequest,
    ConflictRequest,
)
from app.collaboration.services.collaboration_service import CollaborationService

router = APIRouter()


@router.post("/session", response_model=CollaborationSessionResponse)
def create_session(req: CollaborationSessionCreate, db: Session = Depends(get_db)):
    service = CollaborationService(db)
    session = service.create_session(req)
    # Automatically form team for simplicity of API testing
    session = service.form_team(session.session_id)
    return session


@router.get("/session/{session_id}", response_model=CollaborationSessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    service = CollaborationService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/delegate")
def delegate_task(session_id: str, req: DelegateRequest, db: Session = Depends(get_db)):
    service = CollaborationService(db)
    return service.delegate(session_id, req)


@router.post("/negotiate")
def negotiate(session_id: str, req: NegotiateRequest, db: Session = Depends(get_db)):
    service = CollaborationService(db)
    return service.negotiate(session_id, req)


@router.post("/consensus")
def start_consensus(
    session_id: str, req: ConsensusRequest, db: Session = Depends(get_db)
):
    service = CollaborationService(db)
    return service.start_consensus(session_id, req)


@router.post("/conflict")
def raise_conflict(
    session_id: str, req: ConflictRequest, db: Session = Depends(get_db)
):
    service = CollaborationService(db)
    return service.raise_conflict(session_id, req)
