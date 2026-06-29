from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
from app.models.security import User, AuthSession
from app.security.authentication.password_service import password_service
from app.security.authentication.jwt_provider import jwt_provider


class AuthService:
    def authenticate_user(self, db: Session, email: str, password: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="User is inactive")
        if not password_service.verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user

    def create_session(self, db: Session, user: User) -> AuthSession:
        # Create JWT payload
        payload = {"sub": user.id, "tenant_id": user.tenant_id, "email": user.email}
        token = jwt_provider.create_access_token(payload)

        # Store session in DB
        db_session = AuthSession(
            user_id=user.id,
            token=token,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=jwt_provider.expire_minutes),
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session

    def verify_token_and_get_user(self, db: Session, token: str) -> User:
        try:
            payload = jwt_provider.decode_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

        # Check session is valid in DB
        db_session = db.query(AuthSession).filter(AuthSession.token == token).first()
        if not db_session or db_session.is_revoked:
            raise HTTPException(status_code=401, detail="Session revoked or invalid")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="User is inactive")

        return user

    def revoke_session(self, db: Session, token: str) -> None:
        db_session = db.query(AuthSession).filter(AuthSession.token == token).first()
        if db_session:
            db_session.is_revoked = True
            db.commit()


auth_service = AuthService()
