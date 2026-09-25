from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

DEV_PLACEHOLDER_JWT_SECRET = "change-this-development-secret-key-32chars"


class Settings(BaseSettings):
    PROJECT_NAME: str = "UIProof AI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # CORS
    CORS_ORIGINS: List[str] = [
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

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production":
            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == DEV_PLACEHOLDER_JWT_SECRET:
                raise ValueError("JWT_SECRET_KEY must be explicitly configured with a secure secret in production.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
