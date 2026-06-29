from fastapi import APIRouter, Depends
from app.operations.services.operations_service import OperationsService

router = APIRouter(tags=["operations"])

# Singleton service instance
_service = OperationsService()


def get_operations_service() -> OperationsService:
    return _service


@router.get("/health")
def get_health(service: OperationsService = Depends(get_operations_service)):
    return service.get_health()


@router.get("/traces")
def get_traces(service: OperationsService = Depends(get_operations_service)):
    return service.get_traces()


@router.get("/logs")
def get_logs(
    component: str = None,
    severity: str = None,
    trace_id: str = None,
    service: OperationsService = Depends(get_operations_service),
):
    return service.get_logs(component=component, severity=severity, trace_id=trace_id)


@router.get("/metrics")
def get_metrics(service: OperationsService = Depends(get_operations_service)):
    return service.get_metrics()


@router.get("/cost")
def get_cost(service: OperationsService = Depends(get_operations_service)):
    return service.get_cost()


@router.get("/alerts")
def get_alerts(service: OperationsService = Depends(get_operations_service)):
    return service.get_alerts()


@router.get("/analytics")
def get_analytics(service: OperationsService = Depends(get_operations_service)):
    return service.get_analytics()


@router.get("/system")
def get_system(service: OperationsService = Depends(get_operations_service)):
    return service.get_system()


@router.get("/baselines")
def get_baselines(service: OperationsService = Depends(get_operations_service)):
    return service.get_baselines()


@router.get("/profiles")
def get_profiles(service: OperationsService = Depends(get_operations_service)):
    return service.get_profiles()
