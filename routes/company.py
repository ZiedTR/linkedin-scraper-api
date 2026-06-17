from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from cachetools import TTLCache
from services.linkedin_client import linkedin

router = APIRouter(prefix="/company", tags=["Company"])
limiter = Limiter(key_func=get_remote_address)
cache = TTLCache(maxsize=500, ttl=300)

@router.get("/")
@limiter.limit("100/minute")
async def get_company(request: Request, linkedin_url: str):
    key = f"company:{linkedin_url}"
    if key in cache:
        return cache[key]
    data = await linkedin.get("/get-company-details", params={"url": linkedin_url})
    cache[key] = data
    return data

@router.get("/employees")
@limiter.limit("100/minute")
async def get_company_employees(request: Request, linkedin_url: str, start: int = 0):
    key = f"company_employees:{linkedin_url}:{start}"
    if key in cache:
        return cache[key]
    data = await linkedin.get("/get-company-employees", params={"url": linkedin_url, "start": start})
    cache[key] = data
    return data

@router.get("/jobs")
@limiter.limit("100/minute")
async def get_company_jobs(request: Request, linkedin_url: str, start: int = 0):
    key = f"company_jobs:{linkedin_url}:{start}"
    if key in cache:
        return cache[key]
    data = await linkedin.get("/get-company-jobs", params={"url": linkedin_url, "start": start})
    cache[key] = data
    return data

@router.get("/updates")
@limiter.limit("100/minute")
async def get_company_updates(request: Request, linkedin_url: str, start: int = 0):
    key = f"company_updates:{linkedin_url}:{start}"
    if key in cache:
        return cache[key]
    data = await linkedin.get("/get-company-updates", params={"url": linkedin_url, "start": start})
    cache[key] = data
    return data
