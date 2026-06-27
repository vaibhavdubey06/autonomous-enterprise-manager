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
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    QDRANT_TOP_K: int = 10
    RERANK_TOP_K: int = 5

    GITHUB_TOKEN: str = ""

    RECENT_MESSAGE_LIMIT: int = 5
    MEMORY_SEARCH_TOP_K: int = 5
    SUMMARY_TRIGGER_CHARACTERS: int = 8000
    MEMORY_IMPORTANCE_THRESHOLD: float = 0.55
    MEMORY_EXTRACTION_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()