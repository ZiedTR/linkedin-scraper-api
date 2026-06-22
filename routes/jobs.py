from fastapi import APIRouter, Query
from services.linkedin_client import linkedin
from typing import Optional

router = APIRouter(prefix="/jobs", tags=["Job APIs"])

@router.get("/", summary="Get Job Details")
async def get_job(id: str = Query(..., description="LinkedIn Job ID")):
    return await linkedin.get("/get-job-details", params={"id": id})

@router.get("/search", summary="Search Jobs")
async def search_jobs(
    keywords: str = Query(...),
    locationId: Optional[str] = None,
    datePosted: Optional[str] = Query(None, description="past24Hours | pastWeek | pastMonth"),
    jobType: Optional[str] = Query(None, description="fullTime | partTime | contract | internship"),
    experienceLevel: Optional[str] = None,
    onsiteRemote: Optional[str] = Query(None, description="onSite | remote | hybrid"),
    sort: Optional[str] = Query(None, description="mostRecent | mostRelevant"),
    start: int = 0,
):
    params = {k: v for k, v in locals().items() if v is not None}
    return await linkedin.get("/search-jobs", params=params)

@router.get("/search-v2", summary="Search Jobs V2")
async def search_jobs_v2(
    keywords: str = Query(...),
    locationId: Optional[str] = None,
    start: int = 0,
):
    return await linkedin.get("/search-jobs-v2", params={"keywords": keywords, "locationId": locationId, "start": start})

@router.get("/hiring-team", summary="Get Hiring Team")
async def get_hiring_team(id: str = Query(...)):
    return await linkedin.get("/get-hiring-team", params={"id": id})
