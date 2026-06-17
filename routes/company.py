from fastapi import APIRouter, Query
from services.linkedin_client import linkedin
from typing import Optional

router = APIRouter(prefix="/company", tags=["Company APIs"])

@router.get("/", summary="Get Company Details")
async def get_company(username: str = Query(...)):
      return await linkedin.get("/get-company-details", params={"username": username})

@router.get("/by-id", summary="Get Company Details by ID")
async def get_company_by_id(id: str = Query(...)):
      return await linkedin.get("/get-company-details-by-id", params={"id": id})

@router.get("/by-domain", summary="Get Company by Domain")
async def get_company_by_domain(domain: str = Query(..., example="apple.com")):
      return await linkedin.get("/get-company-by-domain", params={"domain": domain})

@router.post("/search", summary="Search Companies")
async def search_companies(keywords: str = Query(...), start: int = 0):
      return await linkedin.post("/search-companies", body={"keywords": keywords, "start": start})

@router.post("/jobs", summary="Get Company Jobs")
async def get_company_jobs(company_id: str = Query(...), start: int = 0):
      return await linkedin.post("/get-company-jobs", body={"companyId": company_id, "start": start})

@router.get("/jobs-count", summary="Get Company Jobs Count")
async def get_jobs_count(username: str = Query(...)):
      return await linkedin.get("/get-company-jobs-count", params={"username": username})

@router.post("/employees-count", summary="Get Company Employees Count")
async def get_employees_count(company_id: str = Query(...)):
      return await linkedin.post("/get-company-employees-count", body={"companyId": company_id})

@router.get("/people-also-viewed", summary="Get Company Pages People Also Viewed")
async def get_people_also_viewed(username: str = Query(...)):
      return await linkedin.get("/get-company-pages-people-also-viewed", params={"username": username})

@router.get("/posts", summary="Get Company Posts")
async def get_company_posts(username: str = Query(...), start: int = 0):
      return await linkedin.get("/get-company-posts", params={"username": username, "start": start})

@router.get("/post-comments", summary="Get Company Post Comments")
async def get_company_post_comments(urn: str = Query(...)):
      return await linkedin.get("/get-company-post-comments", params={"urn": urn})

@router.get("/insights", summary="Get Company Insights PREMIUM")
async def get_company_insights(username: str = Query(...)):
      return await linkedin.get("/get-company-insights", params={"username": username})
  
