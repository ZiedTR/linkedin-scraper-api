"""
Adapter for a generic RapidAPI LinkedIn provider using the classic
"linkedin-data-api" (rockapis-style) endpoint names and the `url`/`username`
convention. Reuses the existing httpx client in services/linkedin_client.py.

This is the default provider and keeps every existing route working if you point
LINKEDIN_BASE_URL / LINKEDIN_RAPIDAPI_HOST at any schema-compatible RapidAPI API.
"""
from __future__ import annotations
from typing import Any

from services.linkedin_client import linkedin
from .base import LinkedInProvider, canonical_profile


def _positions(profile: dict) -> list[dict]:
    raw = (
        (profile.get("position") if isinstance(profile.get("position"), list) else None)
        or profile.get("fullPositions")
        or (profile.get("positions") or {}).get("positionHistory")
        or []
    )
    out = []
    for p in raw:
        if not isinstance(p, dict):
            continue
        out.append({
            "title": p.get("title"),
            "companyName": p.get("companyName") or p.get("company"),
            "start": {"year": (p.get("start") or {}).get("year")},
            "end": {"year": (p.get("end") or {}).get("year")},
        })
    return out


class RapidApiGenericProvider(LinkedInProvider):
    name = "rapidapi_generic"

    async def profile(self, linkedin_url: str) -> dict:
        d = await linkedin.get("/get-profile-data-by-url", params={"url": linkedin_url})
        d = d.get("data", d) if isinstance(d, dict) else {}
        geo = d.get("geo") or {}
        location = geo.get("full") or geo.get("name") if isinstance(geo, dict) else None
        skills = d.get("skills") or []
        return canonical_profile(
            first_name=d.get("firstName"),
            last_name=d.get("lastName"),
            headline=d.get("headline"),
            summary=d.get("summary"),
            profile_picture=d.get("profilePicture"),
            industry=d.get("industryName") or d.get("industry"),
            location=location or d.get("geoLocationName"),
            followers=d.get("followerCount") or d.get("followersCount") or 0,
            connections=d.get("connectionCount") or d.get("connectionsCount") or 0,
            positions=_positions(d),
            educations=d.get("educations") or [],
            skills=skills,
            is_premium=bool(d.get("isPremium")),
            open_to_work=bool(d.get("openToWork") or d.get("isOpenToWork")),
            provider=self.name,
            raw=d,
        )

    async def company(self, linkedin_url: str) -> dict:
        d = await linkedin.get("/get-company-details-by-url", params={"url": linkedin_url})
        data = d.get("data", d) if isinstance(d, dict) else {}
        return {"_provider": self.name, **(data if isinstance(data, dict) else {"data": data})}

    async def profile_posts(self, linkedin_url: str, start: int = 0) -> list[dict]:
        d = await linkedin.get("/get-profile-posts", params={"url": linkedin_url, "start": start})
        items = (d or {}).get("data", []) if isinstance(d, dict) else []
        return [
            {"text": p.get("text") or p.get("commentary") or p.get("content"), "_raw": p}
            for p in items
        ]

    async def profile_recommendations(self, linkedin_url: str) -> list[dict]:
        d = await linkedin.get("/get-profile-recommendations", params={"url": linkedin_url})
        return (d or {}).get("data", []) if isinstance(d, dict) else []

    async def close(self) -> None:
        await linkedin.close()
