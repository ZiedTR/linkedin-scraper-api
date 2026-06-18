from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    # RapidAPI
    rapidapi_key: str = ""
    rapidapi_host: str = "linkedin-data-api.p.rapidapi.com"
    base_url: str = "https://linkedin-data-api.p.rapidapi.com"

    # HTTP Client
    request_timeout: float = 20.0
    max_retries: int = 4
    backoff_base: float = 0.5

    # Cache
    cache_ttl: int = 900
    cache_maxsize: int = 2000

    # Rate Limiting
    rate_limit: str = "100/minute"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "LINKEDIN_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
