from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    # Data provider selection. The upstream data source is pluggable: point it
    # at any RapidAPI LinkedIn provider today (set host + base_url + key), or a
    # licensed provider (Coresignal / People Data Labs) later, without touching
    # the routes. Enrichment endpoints (/enrich/*) work regardless of provider.
    provider: str = "rapidapi_generic"

    # RapidAPI. Set `rapidapi_host` (and key); base_url auto-derives from it, so
    # switching provider = change host + provider only. Set base_url explicitly
    # to override (e.g. a non-RapidAPI licensed provider).
    rapidapi_key: str = ""
    rapidapi_host: str = "linkedin-data-api.p.rapidapi.com"
    base_url: str = ""

    @property
    def resolved_base_url(self) -> str:
        return self.base_url or f"https://{self.rapidapi_host}"

    # People Data Labs (provider=pdl). Free tier: 100 lookups/month, no card.
    pdl_api_key: str = ""
    pdl_base_url: str = ""

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
