from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///db.sqlite3"
    app_title: str = "Task Tracker API"

    secret_key: str = "dev-only-insecure-secret-key-change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expiry_days: int = 30


settings = Settings()
