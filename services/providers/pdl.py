"""
Adapter for People Data Labs (PDL) Person Enrichment API.

Why PDL: a genuinely free, reliable option — 100 enrichments/month free, no card,
licensed dataset (not a scraper that vanishes). Enriches by LinkedIn URL.

Endpoint : GET https://api.peopledatalabs.com/v5/person/enrich
Auth     : header  X-Api-Key: <PDL key>   (separate from RapidAPI)
Lookup   : ?profile=<linkedin url or linkedin.com/in/username>

Activate with:
    LINKEDIN_PROVIDER=pdl
    LINKEDIN_PDL_API_KEY=<your PDL API key>   (get one free at peopledatalabs.com)

Note: PDL returns licensed dataset records, not a live scrape — profile fields
(name, title, experience, education, skills, location) are real; it does NOT
expose follower/connection counts or posts, so those enrichment components
degrade gracefully. Reselling raw PDL records requires a PDL license; the free
tier is for testing / your own use.
"""
from __future__ import annotations
from typing import Any, Optional
import httpx

from config import get_settings
from .base import LinkedInProvider, ProviderError, ProviderCapabilityError, canonical_profile

settings = get_settings()
PDL_BASE = "https://api.peopledatalabs.com"


def _pick(d: dict, *keys, default=None):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", [], {}):
            return v
    return default


def _year(value: Any) -> Optional[int]:
    if isinstance(value, str) and value[:4].isdigit():
        return int(value[:4])
    if isinstance(value, (int, float)):
        return int(value)
    return None


def _name(v: Any) -> Optional[str]:
    # PDL nests some values as {"name": "..."}; accept plain strings too.
    if isinstance(v, dict):
        return v.get("name")
    return v if isinstance(v, str) else None


class PDLProvider(LinkedInProvider):
    name = "pdl"

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=settings.pdl_base_url or PDL_BASE,
                timeout=settings.request_timeout,
                headers={"X-Api-Key": settings.pdl_api_key, "Accept": "application/json"},
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._client

    async def profile(self, linkedin_url: str) -> dict:
        if not settings.pdl_api_key:
            raise ProviderError("LINKEDIN_PDL_API_KEY is not set", status=401)
        resp = await self.client.get(
            "/v5/person/enrich",
            params={"profile": linkedin_url, "min_likelihood": 2},
        )
        if resp.status_code == 401:
            raise ProviderError("PDL: invalid API key", status=401)
        if resp.status_code == 402:
            raise ProviderError("PDL: quota exhausted (free tier is 100/month)", status=402)
        if resp.status_code == 404:
            raise ProviderError("PDL: no matching person for this URL", status=404)
        resp.raise_for_status()
        body = resp.json()
        d = body.get("data", body) if isinstance(body, dict) else {}

        positions = []
        for e in _pick(d, "experience", default=[]) or []:
            positions.append({
                "title": _name(_pick(e, "title", "job_title")),
                "companyName": _name(_pick(e, "company")),
                "start": {"year": _year(_pick(e, "start_date"))},
                "end": {"year": _year(_pick(e, "end_date"))},
            })
        educations = [
            {"schoolName": _name(_pick(ed, "school"))}
            for ed in _pick(d, "education", default=[]) or []
        ]
        return canonical_profile(
            first_name=_pick(d, "first_name"),
            last_name=_pick(d, "last_name"),
            headline=_pick(d, "headline", "job_title"),
            summary=_pick(d, "summary"),
            profile_picture=None,
            industry=_pick(d, "industry", "job_company_industry"),
            location=_pick(d, "location_name", "job_company_location_name"),
            followers=0,  # PDL does not expose follower/connection counts
            connections=0,
            positions=positions,
            educations=educations,
            skills=_pick(d, "skills", default=[]),
            is_premium=False,
            open_to_work=False,
            provider=self.name,
            raw=d,
        )

    async def profile_posts(self, linkedin_url: str, start: int = 0) -> list[dict]:
        raise ProviderCapabilityError(self.name, "profile_posts")

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
