import os
import secrets
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

    # CORS - comma-separated list of allowed origins (no wildcard in production)
    CORS_ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    # Auth & Tokens
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(48) if os.getenv("ENV") != "dev" else "dev-only-insecure-jwt-key-do-not-use-in-prod",
        description="Secret key for JWT signing. MUST be set via env var in production.",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Cryptography
    SECRETS_ENCRYPTION_KEY: str = Field(
        default_factory=lambda: __import__("cryptography.fernet", fromlist=["Fernet"]).Fernet.generate_key().decode(),
        description="AES-256 key for envelope encryption. Auto-generated if not set.",
    )

    # OpenTelemetry
    OTEL_SERVICE_NAME: str = "neuromesh-core"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"

    # LLM Settings
    OLLAMA_HOST: str = Field(default="http://localhost:11434")
    OPENAI_API_KEY: str | None = None
    OPENAI_API_BASE: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        """Parsed list of allowed CORS origins."""
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

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

    def validate_production_secrets(self) -> list[str]:
        """Returns a list of warnings for missing production secrets.
        
        Raises RuntimeError in prod if critical secrets are using insecure defaults.
        """
        warnings = []
        if self.ENV == "prod":
            if "dev-only" in self.JWT_SECRET_KEY:
                msg = "JWT_SECRET_KEY is using an insecure dev default. Set a real secret via env var."
                warnings.append(msg)
                raise RuntimeError(f"SECURITY BLOCKER: {msg}")
            if len(self.JWT_SECRET_KEY) < 32:
                msg = "JWT_SECRET_KEY is too short (< 32 chars). Generate a strong key."
                warnings.append(msg)
                raise RuntimeError(f"SECURITY BLOCKER: {msg}")
        return warnings


# Global settings singleton
settings = Settings()
