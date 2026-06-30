from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.security.identity.identity_context import get_current_identity
from app.security.authorization.rbac_engine import rbac_engine
from app.security.authorization.abac_engine import abac_engine
from app.security.authorization.permission_registry import permission_registry
from fastapi import HTTPException


class AuthorizationDecision(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    missing_permissions: List[str] = []


class AuthorizationPipeline:
    def authorize(
        self,
        required_permissions: Optional[List[str]] = None,
        resource_attributes: Optional[Dict[str, Any]] = None,
        required_attributes: Optional[Dict[str, Any]] = None,
        capability_name: Optional[str] = None,
    ) -> AuthorizationDecision:

        identity = get_current_identity()
        if not identity:
            return AuthorizationDecision(
                allowed=False, reason="No identity context found"
            )

        required_permissions = required_permissions or []

        # 1. Expand required permissions based on capability
        if capability_name:
            cap_perms = permission_registry.get_capability_permissions(capability_name)
            required_permissions.extend(cap_perms)

        # 2. RBAC Evaluation
        if required_permissions:
            rbac_allowed = rbac_engine.evaluate(identity, required_permissions)
            if not rbac_allowed:
                # Find exactly which permissions are missing for better audit logging
                missing = [
                    p
                    for p in required_permissions
                    if p not in identity.permissions
                    and "admin" not in identity.roles
                    and "*" not in identity.permissions
                ]
                return AuthorizationDecision(
                    allowed=False,
                    reason="RBAC permission denied",
                    missing_permissions=missing,
                )

        # 3. ABAC Evaluation
        if required_attributes:
            abac_allowed = abac_engine.evaluate(
                identity, resource_attributes or {}, required_attributes
            )
            if not abac_allowed:
                return AuthorizationDecision(
                    allowed=False, reason="ABAC conditions not met"
                )

        return AuthorizationDecision(allowed=True)

    def authorize_or_raise(self, **kwargs):
        decision = self.authorize(**kwargs)
        if not decision.allowed:
            raise HTTPException(status_code=403, detail=decision.reason)


authorization_pipeline = AuthorizationPipeline()
