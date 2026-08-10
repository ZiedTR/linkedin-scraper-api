"""
Adapter for "Fresh LinkedIn Profile Data" on RapidAPI.

NOTE ON FIELD MAPPING: this maps Fresh's response into our canonical shape using
defensive multi-key extraction, because the exact field names must be confirmed
against a live response (network to RapidAPI is unavailable from the build env).
Extraction tries several plausible keys and degrades gracefully, so a partial
mismatch yields empty fields rather than a crash. Confirm one real response and
adjust the candidate lists below if needed.

Activate with:
    LINKEDIN_PROVIDER=fresh
    LINKEDIN_RAPIDAPI_HOST=fresh-linkedin-profile-data.p.rapidapi.com
    LINKEDIN_BASE_URL=https://fresh-linkedin-profile-data.p.rapidapi.com
    LINKEDIN_RAPIDAPI_KEY=<your key>
"""
from __future__ import annotations
from typing import Any, Optional
import httpx

from config import get_settings
from .base import LinkedInProvider, ProviderError, canonical_profile

settings = get_settings()


def _pick(d: dict, *keys, default=None):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", [], {}):
            return v
    return default


def _year(value: Any) -> Optional[int]:
    if isinstance(value, dict):
        return value.get("year") or value.get("Year")
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value[:4].isdigit():
        return int(value[:4])
    return None


class FreshProvider(LinkedInProvider):
    name = "fresh"

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=settings.base_url,
                timeout=settings.request_timeout,
                headers={
                    "x-rapidapi-key": settings.rapidapi_key,
                    "x-rapidapi-host": settings.rapidapi_host,
                },
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._client

    async def _get(self, path: str, params: dict) -> dict:
        resp = await self.client.get(path, params=params)
        if resp.status_code == 403:
            raise ProviderError("Fresh: access denied — check key/subscription", status=403)
        if resp.status_code == 404:
            raise ProviderError("Fresh: resource not found", status=404)
        resp.raise_for_status()
        body = resp.json()
        return body.get("data", body) if isinstance(body, dict) else {}

    async def profile(self, linkedin_url: str) -> dict:
        d = await self._get(
            "/get-linkedin-profile",
            {"linkedin_url": linkedin_url, "include_skills": "true"},
        )
        positions = []
        for e in _pick(d, "experiences", "positions", "experience", default=[]) or []:
            positions.append({
                "title": _pick(e, "title", "position", "role"),
                "companyName": _pick(e, "company", "companyName", "company_name"),
                "start": {"year": _year(_pick(e, "starts_at", "start", "startDate"))},
                "end": {"year": _year(_pick(e, "ends_at", "end", "endDate"))},
            })
        educations = [
            {"schoolName": _pick(ed, "school", "schoolName", "school_name")}
            for ed in _pick(d, "educations", "education", default=[]) or []
        ]
        return canonical_profile(
            first_name=_pick(d, "first_name", "firstName"),
            last_name=_pick(d, "last_name", "lastName"),
            headline=_pick(d, "headline", "sub_title", "occupation"),
            summary=_pick(d, "about", "summary", "description"),
            profile_picture=_pick(d, "profile_image_url", "profilePicture", "photo_url"),
            industry=_pick(d, "company_industry", "industry", "industryName"),
            location=_pick(d, "location", "city", "geo", "geoLocationName"),
            followers=_pick(d, "follower_count", "followers", "followersCount", default=0),
            connections=_pick(d, "connection_count", "connections", "connectionsCount", default=0),
            positions=positions,
            educations=educations,
            skills=_pick(d, "skills", default=[]),
            is_premium=bool(_pick(d, "is_premium", "premium", default=False)),
            open_to_work=bool(_pick(d, "open_to_work", "openToWork", default=False)),
            provider=self.name,
            raw=d,
        )

    async def company(self, linkedin_url: str) -> dict:
        d = await self._get("/get-company-by-linkedinurl", {"linkedin_url": linkedin_url})
        return {"_provider": self.name, **(d if isinstance(d, dict) else {"data": d})}

    async def profile_posts(self, linkedin_url: str, start: int = 0) -> list[dict]:
        d = await self._get("/get-profile-posts", {"linkedin_url": linkedin_url})
        items = d if isinstance(d, list) else _pick(d, "posts", "data", default=[])
        return [
            {"text": _pick(p, "text", "commentary", "content"), "_raw": p}
            for p in (items or [])
        ]

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
