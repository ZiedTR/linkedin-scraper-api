import asyncio
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.providers import get_provider
from services.ai_service import (
    score_influence, analyze_career_trajectory, analyze_sentiment
)

router = APIRouter(prefix="/ai", tags=["AI Enrichment ⭐"])
limiter = Limiter(key_func=get_remote_address)


def _texts(posts: list[dict], limit: int | None = None) -> list[str]:
    out = [p.get("text") for p in (posts or []) if p.get("text")]
    return out[:limit] if limit else out


@router.get("/score", summary="[UNIQUE] AI influence score for a profile (0-100)")
@limiter.limit("30/minute")
async def ai_score(request: Request, linkedin_url: str):
    """
    AI-computed influence score (0–100) with breakdown by followers, connections,
    content activity, profile completeness, recommendations.
    """
    provider = get_provider()
    profile, posts, recs = await asyncio.gather(
        provider.profile(linkedin_url),
        provider.profile_posts(linkedin_url),
        provider.profile_recommendations(linkedin_url),
        return_exceptions=True,
    )
    profile = {} if isinstance(profile, Exception) else profile
    posts = [] if isinstance(posts, Exception) else posts
    recs = [] if isinstance(recs, Exception) else recs
    followers = {
        "followersCount": profile.get("followersCount", 0),
        "connectionsCount": profile.get("connectionsCount", 0),
    }
    result = score_influence(profile, followers, posts, recs)
    return {"linkedinUrl": linkedin_url, **result}


@router.get("/career-trajectory", summary="[UNIQUE] Career trajectory & next move prediction")
@limiter.limit("30/minute")
async def career_trajectory(request: Request, linkedin_url: str):
    """Predicts likely next job move and progression direction from work history."""
    profile = await get_provider().profile(linkedin_url)
    trajectory = analyze_career_trajectory(profile.get("positions") or [])
    return {"linkedinUrl": linkedin_url, "trajectory": trajectory}


@router.get("/sentiment", summary="[UNIQUE] Sentiment analysis of recent posts")
@limiter.limit("30/minute")
async def sentiment(request: Request, linkedin_url: str, limit: int = 10):
    """Sentiment (positive / negative / neutral) over the last N posts."""
    limit = min(limit, 50)
    posts = await get_provider().profile_posts(linkedin_url)
    return {"linkedinUrl": linkedin_url, **analyze_sentiment(_texts(posts, limit))}


@router.get("/intent", summary="[UNIQUE] Job-seeking or hiring intent signals")
@limiter.limit("30/minute")
async def intent_signals(request: Request, linkedin_url: str):
    """Detects open-to-work / actively-hiring signals from profile + recent posts."""
    provider = get_provider()
    profile, posts = await asyncio.gather(
        provider.profile(linkedin_url),
        provider.profile_posts(linkedin_url),
        return_exceptions=True,
    )
    profile = {} if isinstance(profile, Exception) else profile
    posts = [] if isinstance(posts, Exception) else posts

    all_text = " ".join(filter(None, [
        (profile.get("headline") or "").lower(),
        (profile.get("summary") or "").lower(),
        " ".join(_texts(posts, 5)).lower(),
    ]))
    open_to_work = profile.get("openToWork") is True or any(
        kw in all_text for kw in ["open to", "looking for", "seeking new", "available for"]
    )
    actively_hiring = any(
        kw in all_text for kw in ["we're hiring", "join our team", "open position", "job opening", "now hiring"]
    )
    return {
        "linkedinUrl": linkedin_url,
        "signals": {"openToWork": open_to_work, "activelyHiring": actively_hiring},
        "confidence": "high" if (open_to_work or actively_hiring) else "low",
    }
