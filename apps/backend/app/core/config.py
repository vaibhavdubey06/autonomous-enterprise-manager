from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from app.platform.configuration.runtime_profiles import EnvironmentProfile
from app.platform.configuration.configuration_service import ConfigurationService

# We determine the profile from the environment variable (or default to DEV)
current_profile_str = os.getenv("APP_ENV", "development")
try:
    current_profile = EnvironmentProfile(current_profile_str)
except ValueError:
    current_profile = EnvironmentProfile.DEVELOPMENT

config_service = ConfigurationService(current_profile)


class Settings(BaseSettings):
    APP_NAME: str = "Autonomous Enterprise Manager"

    POSTGRES_HOST: str = config_service.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "enterprise_manager"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "admin"

    QDRANT_URL: str = config_service.get("QDRANT_URL", "http://qdrant:6333")

    REDIS_URL: str = config_service.get("REDIS_URL", "redis://localhost:6379")

    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    QDRANT_TOP_K: int = 10
    RERANK_TOP_K: int = 5

    GITHUB_TOKEN: str = ""

    JWT_SECRET_KEY: str = "super-secret-default-key-please-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 1 day

    RECENT_MESSAGE_LIMIT: int = 5
    MEMORY_SEARCH_TOP_K: int = 5
    SUMMARY_TRIGGER_CHARACTERS: int = 8000
    MEMORY_IMPORTANCE_THRESHOLD: float = 0.55
    MEMORY_EXTRACTION_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
