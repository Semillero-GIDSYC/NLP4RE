import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Configuración del sistema con soporte multi-LLM."""

    APP_NAME: str = "NLP4RE - Requirements Analysis System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "secretpassword"
    POSTGRES_DB: str = "requirements_db"

    LLM_PROVIDER: str = "local" # For embeddings
    GENERATION_LLM_PROVIDER: str = "gemini" # For generation tasks
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "models/gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    LOCAL_MODELS_API: str = "http://localhost:1234/v1/"
    LOCAL_MODEL: str = "google/gemma-3-4b:2"
    LOCAL_EMBEDDER_MODEL: str = "text-embedding-embeddinggemma-300m"

    LLM_TEMPERATURE: float = 0.1
    RETRIEVER_K: int = 3

    DOCS_DIR: str = Field(default="/app/docs")

    @property
    def database_url(self) -> str:
        """URL de conexión a PostgreSQL."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def async_database_url(self) -> str:
        """URL de conexión async (para futuro uso)."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive = True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Singleton de Settings cacheado."""
    return Settings()
