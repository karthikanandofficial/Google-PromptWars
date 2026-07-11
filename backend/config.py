from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator

# Resolve .env relative to this file's directory (backend/), not cwd
_ENV_FILE = Path(__file__).parent / ".env"


class Settings(BaseSettings):
    GEMINI_API_KEY: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_ACCOUNT_SID: str
    # One of these two must be set: path to JSON file, or base64-encoded JSON content
    FIREBASE_CREDENTIALS_PATH: str = ""
    FIREBASE_CREDENTIALS_JSON: str = ""  # base64-encoded; used on Render where file mounts aren't free
    ENVIRONMENT: str = "development"

    @field_validator("GEMINI_API_KEY", "TWILIO_AUTH_TOKEN", "TWILIO_ACCOUNT_SID")
    @classmethod
    def must_not_be_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return v

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8"}


settings = Settings()
