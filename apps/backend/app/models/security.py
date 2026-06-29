from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.core.database import Base


def get_uuid():
    return str(uuid.uuid4())


def get_utc_now():
    return datetime.now(timezone.utc)


# Association tables for RBAC
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "role_id", String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id", String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "permission_id",
        String,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=get_uuid)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(
        DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now
    )

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship(
        "APIKey", back_populates="tenant", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=get_uuid)
    tenant_id = Column(
        String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_service_account = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(
        DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now
    )

    tenant = relationship("Tenant", back_populates="users")
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    sessions = relationship(
        "AuthSession", back_populates="user", cascade="all, delete-orphan"
    )
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=get_uuid)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)

    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, default=get_uuid)
    name = Column(
        String, nullable=False, unique=True
    )  # e.g., "github.read", "workflow.execute"
    description = Column(String, nullable=True)

    roles = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(String, primary_key=True, default=get_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, nullable=False, unique=True, index=True)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    user = relationship("User", back_populates="sessions")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=get_uuid)
    tenant_id = Column(
        String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )  # Can be bound to user or just tenant
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False, unique=True, index=True)
    scopes = Column(JSON, nullable=True)  # List of permission strings
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    tenant = relationship("Tenant", back_populates="api_keys")
    user = relationship("User", back_populates="api_keys")


class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id = Column(String, primary_key=True, default=get_uuid)
    tenant_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    event_type = Column(
        String, nullable=False, index=True
    )  # e.g. AuthenticationSucceeded, PermissionDenied
    resource = Column(String, nullable=True)
    action = Column(String, nullable=True)
    status = Column(String, nullable=False)  # success, failure
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, index=True)
