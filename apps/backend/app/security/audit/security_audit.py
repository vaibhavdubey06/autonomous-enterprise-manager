from sqlalchemy.orm import Session
from app.models.security import SecurityAuditLog
from app.security.identity.identity_context import get_current_identity
from typing import Optional, Dict, Any


class SecurityAuditService:
    def log_event(
        self,
        db: Session,
        event_type: str,
        action: str,
        status: str,
        resource: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        identity = get_current_identity()
        tenant_id = identity.tenant_id if identity else None
        user_id = identity.id if identity else None

        # In a real setup, request_ip comes from context too
        audit_entry = SecurityAuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            action=action,
            status=status,
            resource=resource,
            metadata_json=metadata,
        )
        db.add(audit_entry)
        db.commit()


security_audit = SecurityAuditService()
