from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from cachetools import TTLCache
from services.linkedin_client import linkedin

router = APIRouter(prefix="/profile", tags=["Profile"])
limiter = Limiter(key_func=get_remote_address)
cache = TTLCache(maxsize=500, ttl=300)

@router.get("/")
@limiter.limit("100/minute")
async def get_profile(request: Request, linkedin_url: str):
    key = f"profile:{linkedin_url}"
    if key in cache:
        return cache[key]
    data = await linkedin.get("/get-profile-data-by-url", params={"url": linkedin_url})
    cache[key] = data
    return data

@router.get("/posts")
@limiter.limit("100/minute")
async def get_profile_posts(request: Request, linkedin_url: str, start: int = 0):
    key = f"profile_posts:{linkedin_url}:{start}"
    if key in cache:
        return cache[key]
    data = await linkedin.get("/get-profile-posts", params={"url": linkedin_url, "start": start})
    cache[key] = data
    return data

@router.get("/skills")
@limiter.limit("100/minute")
async def get_profile_skills(request: Request, linkedin_url: str):
    key = f"profile_skills:{linkedin_url}"
    if key in cache:
        return cache[key]
    data = await linkedin.get("/get-profile-skills", params={"url": linkedin_url})
    cache[key] = data
    return data

@router.get("/experiences")
@limiter.limit("100/minute")
async def get_profile_experiences(request: Request, linkedin_url: str):
    key = f"profile_exp:{linkedin_url}"
    if key in cache:
        return cache[key]
    data = await linkedin.get("/get-profile-experience", params={"url": linkedin_url})
    cache[key] = data
    return data

@router.get("/educations")
@limiter.limit("100/minute")
async def get_profile_educations(request: Request, linkedin_url: str):
    key = f"profile_edu:{linkedin_url}"
    if key in cache:
        return cache[key]
    data = await linkedin.get("/get-profile-education", params={"url": linkedin_url})
    cache[key] = data
    return data
