#is the typed Settings object that reads values out of .env and validates them. 
# It's your single source of truth for configuration — the rest of the code asks settings.
# database_url instead of reaching into environment variables directly, so config lives in exactly one spot.
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/switchyard"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()