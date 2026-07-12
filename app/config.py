from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./pronunciation_coach.db"
    cors_origins: str = "*"
    retention_days: int = 30
    min_duration_sec: float = 30.0
    max_duration_sec: float = 45.0
    max_upload_bytes: int = 15 * 1024 * 1024
    whisper_model: str = "small.en"
    whisper_compute_type: str = "int8"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    hf_space_region: str = "us-east-1"
    supabase_region: str = "ap-south-1"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
