import os
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    ENV: Literal["dev", "staging", "prod"] = "dev"
    DEBUG: bool = True

    # PostgreSQL Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://neuromesh:neuromesh_secure_pass@localhost:5432/neuromesh_db"
    )

    # Redis Queue & Cache
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Qdrant Vector DB
    QDRANT_URL: str = Field(default="http://localhost:6333")

    # Object Storage (MinIO / S3)
    STORAGE_ENDPOINT: str = Field(default="localhost:9000")
    STORAGE_ACCESS_KEY: str = Field(default="neuromesh_root")
    STORAGE_SECRET_KEY: str = Field(default="neuromesh_root_secure_pass")
    STORAGE_SECURE: bool = False
    STORAGE_BUCKET_NAME: str = Field(default="neuromesh-artifacts")

    # Auth & Tokens
    JWT_SECRET_KEY: str = Field(
        default="neuromesh_super_secret_jwt_sign_key_change_me_in_production"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Cryptography
    SECRETS_ENCRYPTION_KEY: str = Field(
        default="WjVnd1B4NzdWUWNJU2pIejh0Tk9jREp0UWxVbWpLczI="
    )

    # OpenTelemetry
    OTEL_SERVICE_NAME: str = "neuromesh-core"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"

    # LLM Settings
    OLLAMA_HOST: str = Field(default="http://localhost:11434")
    OPENAI_API_KEY: str | None = None
    OPENAI_API_BASE: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string starting with postgresql")
        return v

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if not v.startswith("redis"):
            raise ValueError("REDIS_URL must start with 'redis://' or 'rediss://'")
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            import warnings
            warnings.warn(
                "JWT_SECRET_KEY is less than 32 characters. This is unsafe for production environments.",
                UserWarning,
            )
        return v


# Global settings singleton
settings = Settings()
