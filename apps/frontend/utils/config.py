import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://backend:8000")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
