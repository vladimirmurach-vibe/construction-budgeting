from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "СВОД — бюджетирование строительных объектов"
    database_url: str = "sqlite:///./test.db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    reports_dir: Path = Path("reports")
    imports_dir: Path = Path("imports")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
