from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_user: str = "roleplay"
    postgres_password: str = "roleplay_dev"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "roleplay_chat"

    redis_host: str = "localhost"
    redis_port: int = 6379

    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.85

    # Memory settings
    memory_enabled: bool = True
    memory_embedding_model: str = "BAAI/bge-small-zh-v1.5"
    memory_embedding_dimension: int = 512
    memory_max_per_query: int = 5
    memory_token_budget: int = 1500
    memory_decay_halflife_days: float = 30.0
    memory_extraction_min_messages: int = 6

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"


settings = Settings()
