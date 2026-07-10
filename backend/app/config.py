from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"
    storage_root: Path = Path("backend/storage")
    max_upload_size_mb: int = Field(default=25, ge=1, le=200)
    allowed_origins: list[str] = ["http://localhost:3000"]

    llm_provider: Literal["groq", "fake"] = "fake"
    llm_model: str = "llama-3.1-8b-instant"
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    llm_max_retries: int = Field(default=1, ge=0, le=5)
    llm_max_concurrency: int = Field(default=4, ge=1, le=32)
    groq_api_key: str | None = None

    ocr_enabled: bool = True
    ocr_language: str = "eng"
    ocr_dpi: int = Field(default=200, ge=72, le=400)
    ocr_max_concurrency: int = Field(default=2, ge=1, le=8)

    parser_version: str = "phase1-parser-v1"
    chunker_version: str = "phase1-chunker-v1"
    clause_prompt_version: str = "clause-extraction-v1"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def active_llm_api_key(self) -> str | None:
        return self.llm_api_key or self.groq_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
