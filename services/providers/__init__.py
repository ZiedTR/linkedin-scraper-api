"""Provider factory. Selected by the LINKEDIN_PROVIDER setting."""
from __future__ import annotations
from functools import lru_cache

from config import get_settings
from .base import (
    LinkedInProvider,
    ProviderError,
    ProviderCapabilityError,
    canonical_profile,
)

__all__ = [
    "LinkedInProvider",
    "ProviderError",
    "ProviderCapabilityError",
    "canonical_profile",
    "get_provider",
]


@lru_cache
def get_provider() -> LinkedInProvider:
    name = (get_settings().provider or "rapidapi_generic").lower()
    if name == "fresh":
        from .fresh import FreshProvider
        return FreshProvider()
    if name in ("rapidapi_generic", "rapidapi", "generic", "rockapis"):
        from .rapidapi_generic import RapidApiGenericProvider
        return RapidApiGenericProvider()
    raise ProviderError(f"Unknown LINKEDIN_PROVIDER '{name}'", status=500)
