from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.database import SessionLocal
from app.security.authentication.auth_service import auth_service
from app.security.identity.identity_context import SecurityContext, set_security_context
from app.security.identity.identity_models import HumanUser
from app.security.api.rate_limiter import global_rate_limiter
import traceback


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        # 1. Rate Limiting
        if global_rate_limiter.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429, content={"detail": "Too Many Requests"}
            )

        # 2. Extract Token
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        # 3. Create basic context
        ctx = SecurityContext(request_ip=client_ip)

        # 4. Authenticate if token present
        if token:
            db = SessionLocal()
            try:
                user = auth_service.verify_token_and_get_user(db, token)
                # Build Identity
                # Need to load roles/permissions from DB, we do a simple mapping here
                roles = [r.name for r in user.roles]
                permissions = []
                for role in user.roles:
                    for p in role.permissions:
                        permissions.append(p.name)

                identity = HumanUser(
                    id=user.id,
                    tenant_id=user.tenant_id,
                    email=user.email,
                    roles=roles,
                    permissions=permissions,
                )
                ctx.identity = identity
                ctx.session_id = (
                    token  # Using token as session_id for simplicity in this context
                )
            except Exception:
                # If authentication fails, we don't abort immediately because some endpoints
                # (like /login or /docs) don't require auth. We just leave identity as None.
                # If they hit a protected route, Depends() will catch it.
                pass
            finally:
                db.close()

        # 5. Inject Context
        set_security_context(ctx)

        # 6. Proceed
        try:
            response = await call_next(request)
            return response
        except Exception:
            traceback.print_exc()
            return JSONResponse(
                status_code=500, content={"detail": "Internal Server Error"}
            )
