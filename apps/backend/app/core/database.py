from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Autonomous Enterprise Manager"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "enterprise_manager"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "admin"

    QDRANT_URL: str = "http://localhost:6333"

    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()