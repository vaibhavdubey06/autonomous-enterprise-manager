from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.integrations.services.integration_service import integration_service
from pydantic import BaseModel

router = APIRouter(tags=["Integrations"])


# A mock for user tenant context since we don't have the full Auth layer wired to endpoints here.
def get_current_tenant() -> str:
    # In a real app this uses Dependency Injection from SecurityMiddleware
    from app.security.identity.identity_context import get_current_identity

    identity = get_current_identity()
    if identity:
        return identity.tenant_id
    return "00000000-0000-0000-0000-000000000000"


@router.get("")
def list_integrations():
    return integration_service.list_available_connectors()


@router.get("/{connector}")
def get_integration(connector: str, tenant_id: str = Depends(get_current_tenant)):
    connector_id = f"{connector}_instance"
    connectors = integration_service.list_tenant_connectors(tenant_id)
    for c in connectors:
        if c.connector_id == connector_id:
            return c
    raise HTTPException(status_code=404, detail="Connector not configured for tenant")


@router.get("/{connector}/health")
def get_health(connector: str, tenant_id: str = Depends(get_current_tenant)):
    connector_id = f"{connector}_instance"
    health = integration_service.get_health(tenant_id, connector_id)
    return {"health": health}


@router.get("/{connector}/capabilities")
def get_capabilities(connector: str, tenant_id: str = Depends(get_current_tenant)):
    connector_id = f"{connector}_instance"
    caps = integration_service.get_capabilities(tenant_id, connector_id)
    return {"capabilities": caps}


class ConnectRequest(BaseModel):
    auth_type: str
    config_data: Dict[str, Any]


@router.post("/{connector}/connect")
def connect(
    connector: str, req: ConnectRequest, tenant_id: str = Depends(get_current_tenant)
):
    try:
        config = integration_service.connect(
            tenant_id, connector, req.auth_type, req.config_data
        )
        return {"status": "connected", "state": config.state}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{connector}/disconnect")
def disconnect(connector: str, tenant_id: str = Depends(get_current_tenant)):
    connector_id = f"{connector}_instance"
    success = integration_service.disconnect(tenant_id, connector_id)
    if success:
        return {"status": "disconnected"}
    raise HTTPException(status_code=400, detail="Failed to disconnect")


class ExecuteRequest(BaseModel):
    capability: str
    parameters: Dict[str, Any]


@router.post("/{connector}/execute")
def execute(
    connector: str, req: ExecuteRequest, tenant_id: str = Depends(get_current_tenant)
):
    connector_id = f"{connector}_instance"
    response = integration_service.execute(
        tenant_id, connector_id, req.capability, req.parameters
    )
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error_message)
    return response.data


@router.get("/events/all")
def get_events():
    return {"events": []}
