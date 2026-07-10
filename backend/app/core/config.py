from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Бюджетирование строительных объектов"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg2://budget:budget@localhost:5432/construction_budgeting"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    log_level: str = "INFO"
    reports_dir: str = "reports"
    fact_import_dir: str = "imports"

    class Config:
        env_file = ".env"


settings = Settings()
