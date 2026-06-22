import asyncio
from fastapi import APIRouter, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.linkedin_client import linkedin
from services.ai_service import compute_proximity, build_org_chart, classify_level

router = APIRouter(prefix="/network", tags=["Network Graph ⭐"])
limiter = Limiter(key_func=get_remote_address)


class ProximityRequest(BaseModel):
    linkedin_url_a: str
    linkedin_url_b: str


@router.post("/proximity", summary="[UNIQUE] Proximity score between two profiles")
@limiter.limit("20/minute")
async def proximity_score(request: Request, body: ProximityRequest):
    """
    Computes a proximity score (0–100) between two LinkedIn profiles based on
    shared industry, location, headline keywords, and education.
    """
    profile_a, profile_b = await asyncio.gather(
        linkedin.request("/get-profile-data-by-url", params={"url": body.linkedin_url_a}),
        linkedin.request("/get-profile-data-by-url", params={"url": body.linkedin_url_b}),
    )
    result = compute_proximity(profile_a, profile_b)
    return {
        "profileA": body.linkedin_url_a,
        "profileB": body.linkedin_url_b,
        **result,
    }


@router.get("/org-chart", summary="[UNIQUE] Reconstruct company org chart from employee titles")
@limiter.limit("10/minute")
async def org_chart(request: Request, company: str, max_results: int = 40):
    """
    Searches employees of a company and reconstructs a hierarchical org chart
    by grouping titles into seniority levels: executive, VP, director, manager, IC.
    """
    if max_results > 100:
        max_results = 100

    people_data = await linkedin.request(
        "/search-people",
        params={"keywords": company, "company": company, "start": 0},
    )
    people = (people_data.get("data") or [])[:max_results]
    chart = build_org_chart(people)

    return {
        "company": company,
        "totalAnalyzed": len(people),
        "summary": {level: len(members) for level, members in chart.items()},
        "orgChart": chart,
    }


@router.get("/similar", summary="Get profiles similar to a given profile")
@limiter.limit("30/minute")
async def similar_profiles(request: Request, linkedin_url: str):
    """Returns profiles LinkedIn considers similar to the given profile."""
    data = await linkedin.request("/get-similar-profiles", params={"url": linkedin_url})
    return data
