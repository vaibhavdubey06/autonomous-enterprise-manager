from typing import Dict, Any
from app.platform.configuration.runtime_profiles import EnvironmentProfile


class ConfigurationService:
    def __init__(self, profile: EnvironmentProfile):
        self.profile = profile
        # Ideally, we load from SecretManager or env overrides here.
        # For this exercise, we keep a simple dictionary of profiles
        self._overrides: Dict[str, Dict[str, Any]] = {
            EnvironmentProfile.DEVELOPMENT: {
                "REDIS_URL": "redis://localhost:6379",
                "POSTGRES_HOST": "localhost",
                "LOG_LEVEL": "DEBUG",
            },
            EnvironmentProfile.TESTING: {
                "REDIS_URL": "redis://localhost:6379",
                "POSTGRES_HOST": "localhost",
                "LOG_LEVEL": "INFO",
            },
            EnvironmentProfile.PRODUCTION: {
                "REDIS_URL": "redis://redis-master:6379",
                "POSTGRES_HOST": "postgres",
                "LOG_LEVEL": "WARNING",
            },
            EnvironmentProfile.ENTERPRISE: {
                "REDIS_URL": "redis://enterprise-redis:6379",
                "POSTGRES_HOST": "enterprise-postgres",
                "LOG_LEVEL": "INFO",
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        profile_config = self._overrides.get(self.profile, {})
        return profile_config.get(key, default)

    def set_override(self, key: str, value: Any) -> None:
        if self.profile not in self._overrides:
            self._overrides[self.profile] = {}
        self._overrides[self.profile][key] = value
