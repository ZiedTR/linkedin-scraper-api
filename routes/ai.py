import asyncio
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.linkedin_client import linkedin
from services.ai_service import (
    score_influence, analyze_career_trajectory, analyze_sentiment
)

router = APIRouter(prefix="/ai", tags=["AI Enrichment ⭐"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/score", summary="[UNIQUE] AI influence score for a profile (0-100)")
@limiter.limit("30/minute")
async def ai_score(request: Request, linkedin_url: str):
    """
    Returns an AI-computed influence score (0–100) with breakdown by:
    followers, connections, content activity, profile completeness, recommendations.
    **Not available on any other LinkedIn API.**
    """
    profile, followers, posts, recs = await asyncio.gather(
        linkedin.request("/get-profile-data-by-url", params={"url": linkedin_url}),
        linkedin.request("/get-profile-followers", params={"url": linkedin_url}),
        linkedin.request("/get-profile-posts", params={"url": linkedin_url, "start": 0}),
        linkedin.request("/get-profile-recommendations", params={"url": linkedin_url}),
        return_exceptions=True,
    )

    def safe(v, default):
        return default if isinstance(v, Exception) else v

    profile = safe(profile, {})
    followers = safe(followers, {})
    posts_list = safe(posts, {}).get("data", []) if isinstance(posts, dict) else []
    recs_list = safe(recs, {}).get("data", []) if isinstance(recs, dict) else []

    result = score_influence(profile, followers, posts_list, recs_list)
    return {"linkedinUrl": linkedin_url, **result}


@router.get("/career-trajectory", summary="[UNIQUE] Career trajectory & next move prediction")
@limiter.limit("30/minute")
async def career_trajectory(request: Request, linkedin_url: str):
    """
    Analyzes work history to predict when a person is likely to change jobs,
    their career progression direction (upward / lateral), and estimated seniority path.
    """
    profile = await linkedin.request("/get-profile-data-by-url", params={"url": linkedin_url})
    positions = (
        profile.get("positions", {}).get("positionHistory")
        or profile.get("experience")
        or []
    )
    trajectory = analyze_career_trajectory(positions)
    return {"linkedinUrl": linkedin_url, "trajectory": trajectory}


@router.get("/sentiment", summary="[UNIQUE] Sentiment analysis of recent posts")
@limiter.limit("30/minute")
async def sentiment(request: Request, linkedin_url: str, limit: int = 10):
    """
    Runs sentiment analysis (positive / negative / neutral) on the last N posts.
    Returns overall tone, confidence score, and per-post breakdown.
    """
    if limit > 50:
        limit = 50
    posts_data = await linkedin.request("/get-profile-posts", params={"url": linkedin_url, "start": 0})
    posts = (posts_data.get("data") or [])[:limit]
    texts = [
        p.get("text") or p.get("commentary") or p.get("content") or ""
        for p in posts
        if p.get("text") or p.get("commentary") or p.get("content")
    ]
    return {"linkedinUrl": linkedin_url, **analyze_sentiment(texts)}


@router.get("/intent", summary="[UNIQUE] Job-seeking or hiring intent signals")
@limiter.limit("30/minute")
async def intent_signals(request: Request, linkedin_url: str):
    """
    Detects signals indicating if a person is actively looking for a job
    or actively hiring, based on profile keywords and recent post activity.
    """
    profile, posts_data = await asyncio.gather(
        linkedin.request("/get-profile-data-by-url", params={"url": linkedin_url}),
        linkedin.request("/get-profile-posts", params={"url": linkedin_url, "start": 0}),
        return_exceptions=True,
    )
    if isinstance(profile, Exception):
        profile = {}
    if isinstance(posts_data, Exception):
        posts_data = {}

    headline = (profile.get("headline") or "").lower()
    summary = (profile.get("summary") or "").lower()
    recent = " ".join(
        (p.get("text") or "").lower()
        for p in (posts_data.get("data") or [])[:5]
    )
    all_text = f"{headline} {summary} {recent}"

    open_to_work = profile.get("openToWork") is True or any(
        kw in all_text for kw in ["open to", "looking for", "seeking new", "available for"]
    )
    actively_hiring = any(
        kw in all_text for kw in ["we're hiring", "join our team", "open position", "job opening", "now hiring"]
    )

    return {
        "linkedinUrl": linkedin_url,
        "signals": {
            "openToWork": open_to_work,
            "activelyHiring": actively_hiring,
        },
        "confidence": "high" if (open_to_work or actively_hiring) else "low",
    }
