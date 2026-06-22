from fastapi import APIRouter, Query
from services.linkedin_client import linkedin

router = APIRouter(prefix="/location", tags=["Location"])

@router.get("/search", summary="Search Locations")
async def search_locations(query: str = Query(...)):
    return await linkedin.get("/search-locations", params={"query": query})
