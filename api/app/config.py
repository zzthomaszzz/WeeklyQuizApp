from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


API_DIRECTORY = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str
    session_secret: str = ""
    cookie_secure: bool = True
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=API_DIRECTORY / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
