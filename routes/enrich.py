"""
Provider-independent enrichment endpoints ("bring your own data").

These POST endpoints accept raw profile / posts / people JSON supplied by the
caller and return the AI-computed enrichment. They do NOT call any external
LinkedIn data provider, so they:
  - work even while the upstream data source is down or being switched,
  - are fully testable offline,
  - carry lower legal exposure than reselling raw scraped LinkedIn data
    (you sell your computation over data the caller already holds).

The same functions are reused by the GET /ai/* endpoints, which fetch the data
from a provider first. This is the monetizable core of the product.
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.ai_service import (
    score_influence,
    analyze_career_trajectory,
    analyze_sentiment,
    compute_proximity,
    build_org_chart,
)

router = APIRouter(prefix="/enrich", tags=["Enrichment (bring your own data) ⭐"])
limiter = Limiter(key_func=get_remote_address)


def _positions_from(profile: dict | None, positions: list[dict] | None) -> list[dict]:
    if positions:
        return positions
    profile = profile or {}
    return (
        (profile.get("positions") or {}).get("positionHistory")
        or profile.get("fullPositions")
        or profile.get("experience")
        or profile.get("positions")
        or []
    )


def _texts_from(texts: list[str] | None, posts: list[dict] | None) -> list[str]:
    if texts:
        return [t for t in texts if t]
    out: list[str] = []
    for p in posts or []:
        t = p.get("text") or p.get("commentary") or p.get("content")
        if t:
            out.append(t)
    return out


class ScoreRequest(BaseModel):
    profile: dict = Field(default_factory=dict, description="Profile object")
    followers: dict | None = Field(default=None, description="{followersCount, connectionsCount}")
    posts: list[dict] = Field(default_factory=list, description="Recent posts")
    recommendations: list[dict] = Field(default_factory=list, description="Recommendations received")


class CareerRequest(BaseModel):
    positions: list[dict] | None = Field(default=None, description="Work history; or pass `profile`")
    profile: dict | None = Field(default=None, description="Full profile to extract positions from")


class SentimentRequest(BaseModel):
    texts: list[str] | None = Field(default=None, description="Raw post texts; or pass `posts`")
    posts: list[dict] | None = Field(default=None, description="Posts to extract text from")
    limit: int = Field(default=50, ge=1, le=200)


class ProximityRequest(BaseModel):
    profile_a: dict
    profile_b: dict


class OrgChartRequest(BaseModel):
    people: list[dict] = Field(default_factory=list)


@router.post("/score", summary="Influence score (0-100) from supplied profile data")
@limiter.limit("60/minute")
async def enrich_score(request: Request, body: ScoreRequest):
    return score_influence(body.profile, body.followers, body.posts, body.recommendations)


@router.post("/career-trajectory", summary="Career trajectory from supplied work history")
@limiter.limit("60/minute")
async def enrich_career(request: Request, body: CareerRequest):
    positions = _positions_from(body.profile, body.positions)
    return {"trajectory": analyze_career_trajectory(positions)}


@router.post("/sentiment", summary="Sentiment analysis of supplied post texts")
@limiter.limit("60/minute")
async def enrich_sentiment(request: Request, body: SentimentRequest):
    texts = _texts_from(body.texts, body.posts)[: body.limit]
    return analyze_sentiment(texts)


@router.post("/proximity", summary="Proximity score between two supplied profiles")
@limiter.limit("60/minute")
async def enrich_proximity(request: Request, body: ProximityRequest):
    return compute_proximity(body.profile_a, body.profile_b)


@router.post("/org-chart", summary="Reconstruct an org chart from supplied people")
@limiter.limit("60/minute")
async def enrich_org_chart(request: Request, body: OrgChartRequest):
    return build_org_chart(body.people)
