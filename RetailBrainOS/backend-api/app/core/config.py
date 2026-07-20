from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Retail Brain OS Backend"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Development default. Override in .env for production.
DATABASE_URL: str = (
    "postgresql://postgres:postgres@localhost:5432/retail_brain_os"
)

model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns the application settings singleton.
    """
    return Settings()


settings = get_settings()