import os
from typing import Dict, Optional
from app.platform.configuration.runtime_profiles import EnvironmentProfile

DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
DEFAULT_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://frontend:8501")


class ServiceRegistry:
    def __init__(self, profile: EnvironmentProfile):
        self.profile = profile
        self._services: Dict[str, Dict[str, str]] = {
            EnvironmentProfile.DEVELOPMENT: {
                "redis": os.getenv("REDIS_URL", "redis://redis:6379/0"),
                "postgres": os.getenv("POSTGRES_HOST", "postgres")
                + ":"
                + os.getenv("POSTGRES_PORT", "5432"),
                "qdrant": os.getenv("QDRANT_URL", "http://qdrant:6333"),
                "backend": DEFAULT_BACKEND_URL,
                "frontend": DEFAULT_FRONTEND_URL,
            },
            EnvironmentProfile.PRODUCTION: {
                "redis": "redis-master.data.svc.cluster.local:6379",
                "postgres": "postgres.data.svc.cluster.local:5432",
                "qdrant": "qdrant.data.svc.cluster.local:6333",
                "backend": "http://backend.api.svc.cluster.local:80",
                "frontend": "http://frontend.web.svc.cluster.local:80",
            },
        }

    def get_service_url(self, service_name: str) -> Optional[str]:
        # Fallback to dev if profile is testing or not fully populated
        profile_map = self._services.get(
            self.profile, self._services[EnvironmentProfile.DEVELOPMENT]
        )
        return profile_map.get(service_name)
