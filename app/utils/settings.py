from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = Field(...)
    mongodb_db_name: str = Field("adaptive_diagnostic")

    groq_api_key: Optional[str] = Field(None)
    groq_model: str = Field("llama-3.1-8b-instant")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()

