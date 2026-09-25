from pathlib import Path
from typing import List, Union, Any
from pydantic import model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_PLACEHOLDER_JWT_SECRET = "change-this-development-secret-key-32chars"


class Settings(BaseSettings):
    PROJECT_NAME: str = "UIProof AI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]

    # Future AI provider settings
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./uiproof.db"
    POSTGRES_URI: str = "postgresql://postgres:postgres@localhost:5432/uiproof_ai"

    # JWT Security Configuration
    JWT_SECRET_KEY: str = DEV_PLACEHOLDER_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Artifact Storage Configuration
    ARTIFACTS_DIR: str = "artifacts"

    @property
    def artifacts_path(self) -> Path:
        p = Path(self.ARTIFACTS_DIR)
        if p.is_absolute():
            return p
        backend_dir = Path(__file__).resolve().parent.parent
        if p.parts and p.parts[0] == "backend":
            return (backend_dir.parent / p).resolve()
        return (backend_dir / p).resolve()

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if not v.strip():
                return []
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, list):
            return v
        return []

    @model_validator(mode="after")
    def validate_and_normalize_configuration(self) -> "Settings":
        # Normalize DATABASE_URL (postgres:// -> postgresql://)
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgres://"):
                self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)

        if self.ENVIRONMENT.lower() == "production":
            # Default host to 0.0.0.0 in production if left at 127.0.0.1
            if self.HOST == "127.0.0.1":
                self.HOST = "0.0.0.0"

            # Validate JWT secret key
            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == DEV_PLACEHOLDER_JWT_SECRET:
                raise ValueError("JWT_SECRET_KEY must be explicitly configured with a secure secret in production.")

            # Hardened production CORS origins check (strip wildcards & localhost origins)
            forbidden_dev_origins = {
                "*",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:4173",
                "http://127.0.0.1:4173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            }
            self.CORS_ORIGINS = [
                o for o in self.CORS_ORIGINS
                if o not in forbidden_dev_origins and not o.startswith("http://localhost") and not o.startswith("http://127.0.0.1")
            ]

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

