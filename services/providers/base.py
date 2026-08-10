"""
Pluggable data-provider layer.

The app's routes talk to a `LinkedInProvider` that returns a **canonical** shape,
independent of which upstream actually served the data. Swapping providers
(a RapidAPI scraper today, a licensed provider like Coresignal / People Data
Labs tomorrow) is then a config change, not a rewrite.

Canonical profile keys are chosen to match what `services/ai_service.py` already
consumes, so the /ai and /enrich layers work regardless of provider.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class ProviderError(RuntimeError):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


class ProviderCapabilityError(ProviderError):
    """Raised when a provider does not implement a given resource."""

    def __init__(self, provider: str, resource: str):
        super().__init__(
            f"Provider '{provider}' does not support '{resource}'. "
            f"Choose a provider that offers it, or disable this endpoint.",
            status=501,
        )


def canonical_profile(
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    headline: str | None = None,
    summary: str | None = None,
    profile_picture: str | None = None,
    industry: str | None = None,
    location: str | None = None,
    followers: int | None = None,
    connections: int | None = None,
    positions: list[dict] | None = None,
    educations: list[dict] | None = None,
    skills: list[Any] | None = None,
    is_premium: bool = False,
    open_to_work: bool = False,
    provider: str = "",
    raw: Any = None,
) -> dict:
    """Assemble a canonical profile dict with the exact keys ai_service reads."""
    full = " ".join(filter(None, [first_name, last_name])) or None
    return {
        "firstName": first_name,
        "lastName": last_name,
        "fullName": full,
        "headline": headline,
        "summary": summary,
        "profilePicture": profile_picture,
        "industryName": industry,
        "geo": {"name": location} if location else None,
        "geoLocationName": location,
        "followersCount": followers or 0,
        "connectionsCount": connections or 0,
        "positions": positions or [],
        "educations": educations or [],
        "skills": skills or [],
        "isPremium": bool(is_premium),
        "openToWork": bool(open_to_work),
        "_provider": provider,
        "_raw": raw,
    }


class LinkedInProvider(ABC):
    """Interface every data provider adapter implements."""

    name: str = "base"

    @abstractmethod
    async def profile(self, linkedin_url: str) -> dict:
        """Return a canonical profile for a LinkedIn profile URL."""

    async def company(self, linkedin_url: str) -> dict:
        raise ProviderCapabilityError(self.name, "company")

    async def profile_posts(self, linkedin_url: str, start: int = 0) -> list[dict]:
        raise ProviderCapabilityError(self.name, "profile_posts")

    async def profile_recommendations(self, linkedin_url: str) -> list[dict]:
        raise ProviderCapabilityError(self.name, "profile_recommendations")

    async def close(self) -> None:  # pragma: no cover - overridden when needed
        return None
