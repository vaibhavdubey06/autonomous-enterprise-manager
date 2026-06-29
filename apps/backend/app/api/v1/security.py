from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.security.authentication.auth_service import auth_service
from app.security.identity.identity_context import get_current_identity
from app.security.authorization.authorization_pipeline import authorization_pipeline
from pydantic import BaseModel

router = APIRouter(tags=["Security"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, request.email, request.password)
    session = auth_service.create_session(db, user)
    return LoginResponse(access_token=session.token)


@router.post("/logout")
def logout(db: Session = Depends(get_db)):
    # Since we extract the token in middleware and store it in session_id in the identity context:
    identity_ctx = get_current_identity()
    if not identity_ctx:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Actually, we need the raw token to revoke. Let's assume the token is in security_context.session_id
    from app.security.identity.identity_context import get_security_context

    ctx = get_security_context()
    if ctx and ctx.session_id:
        auth_service.revoke_session(db, ctx.session_id)
    return {"status": "success"}


@router.get("/me")
def get_me():
    identity = get_current_identity()
    if not identity:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": identity.id,
        "tenant_id": identity.tenant_id,
        "type": identity.identity_type,
        "roles": identity.roles,
        "permissions": identity.permissions,
    }


@router.get("/audit")
def get_audit_logs(db: Session = Depends(get_db)):
    authorization_pipeline.authorize_or_raise(required_permissions=["security.manage"])
    from app.models.security import SecurityAuditLog

    logs = (
        db.query(SecurityAuditLog)
        .order_by(SecurityAuditLog.timestamp.desc())
        .limit(100)
        .all()
    )
    return logs
