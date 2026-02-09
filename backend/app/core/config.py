"""Application configuration using Pydantic Settings"""
from functools import lru_cache
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "StudyNotesManager"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/studynotes"
    )
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "studynotes"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # JWT
    JWT_SECRET_KEY: str = Field(default="dev-jwt-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:8000"
    )

    # Baidu OCR
    BAIDU_OCR_APP_ID: str = ""
    BAIDU_OCR_API_KEY: str = ""
    BAIDU_OCR_SECRET_KEY: str = ""

    # Aliyun OSS
    ALIYUN_OSS_ACCESS_KEY_ID: str = ""
    ALIYUN_OSS_ACCESS_KEY_SECRET: str = ""
    ALIYUN_OSS_BUCKET_NAME: str = ""
    ALIYUN_OSS_ENDPOINT: str = "oss-cn-hangzhou.aliyuncs.com"

    # DeepSeek AI
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Mindmap Generation
    MINDMAP_MAX_LEVELS: int = 5
    MAX_TOKENS_PER_NOTE: int = 8000
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: Union[str, List[str]] = Field(default="jpg,jpeg,png,pdf")

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse allowed extensions from string or list"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
