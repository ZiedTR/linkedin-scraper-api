import asyncio
import uuid
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.linkedin_client import linkedin
from services.ai_service import score_influence

router = APIRouter(prefix="/batch", tags=["Batch Processing ⭐"])
limiter = Limiter(key_func=get_remote_address)

# In-memory job store (use Redis in production)
_jobs: dict[str, dict] = {}


class BatchRequest(BaseModel):
    linkedin_urls: list[str] = Field(..., max_length=100, example=[
        "https://www.linkedin.com/in/satyanadella/",
        "https://www.linkedin.com/in/billgates/",
    ])
    type: Literal["profile", "score", "company"] = "profile"


async def _run_batch(job_id: str, urls: list[str], job_type: str):
    """Background task — enriches each URL sequentially, respecting rate limits."""
    for url in urls:
        try:
            if job_type == "profile":
                result = await linkedin.request("/get-profile-data-by-url", params={"url": url})
            elif job_type == "score":
                profile, followers = await asyncio.gather(
                    linkedin.request("/get-profile-data-by-url", params={"url": url}),
                    linkedin.request("/get-profile-followers", params={"url": url}),
                    return_exceptions=True,
                )
                p = profile if isinstance(profile, dict) else {}
                f = followers if isinstance(followers, dict) else {}
                result = {"linkedinUrl": url, **score_influence(p, f)}
            elif job_type == "company":
                result = await linkedin.request("/get-company-details-by-url", params={"url": url})
            else:
                result = {}

            _jobs[job_id]["results"].append({"url": url, "data": result})
        except Exception as e:
            _jobs[job_id]["errors"].append({"url": url, "error": str(e)})
        finally:
            _jobs[job_id]["completed"] += 1

        # Throttle between requests to avoid 429
        await asyncio.sleep(0.4)

    _jobs[job_id]["status"] = "completed"
    _jobs[job_id]["completedAt"] = datetime.utcnow().isoformat()


@router.post("/enrich", status_code=202, summary="[UNIQUE] Batch enrich up to 100 profiles async")
@limiter.limit("5/minute")
async def batch_enrich(request: Request, body: BatchRequest, background_tasks: BackgroundTasks):
    """
    Submit a list of LinkedIn URLs for async enrichment (max 100).
    Returns a `jobId` immediately. Poll `/batch/status/{jobId}` for results.

    **type** options:
    - `profile` — full profile data
    - `score` — AI influence score
    - `company` — company details
    """
    if len(body.linkedin_urls) > 100:
        from fastapi import HTTPException
        raise HTTPException(400, "Maximum 100 URLs per batch request")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "jobId": job_id,
        "status": "processing",
        "type": body.type,
        "total": len(body.linkedin_urls),
        "completed": 0,
        "results": [],
        "errors": [],
        "createdAt": datetime.utcnow().isoformat(),
        "completedAt": None,
    }

    background_tasks.add_task(_run_batch, job_id, body.linkedin_urls, body.type)

    return {
        "jobId": job_id,
        "statusUrl": f"/batch/status/{job_id}",
        "total": len(body.linkedin_urls),
        "type": body.type,
        "message": "Job accepted. Poll statusUrl for results.",
    }


@router.get("/status/{job_id}", summary="[UNIQUE] Poll batch job status & partial results")
@limiter.limit("60/minute")
async def batch_status(request: Request, job_id: str):
    """
    Returns current status of a batch job with partial results as they complete.
    `progress` goes from 0% to 100% as each URL is processed.
    """
    if job_id not in _jobs:
        from fastapi import HTTPException
        raise HTTPException(404, "Job not found")

    job = _jobs[job_id]
    progress = round((job["completed"] / max(job["total"], 1)) * 100)
    return {**job, "progress": f"{progress}%"}


@router.get("/jobs", summary="List recent batch jobs (last 20)")
@limiter.limit("30/minute")
async def list_jobs(request: Request):
    """Returns the 20 most recent batch jobs with status summary (no results data)."""
    jobs_summary = [
        {k: v for k, v in j.items() if k not in ("results", "errors")}
        for j in sorted(_jobs.values(), key=lambda x: x["createdAt"], reverse=True)[:20]
    ]
    return {"jobs": jobs_summary, "total": len(_jobs)}
