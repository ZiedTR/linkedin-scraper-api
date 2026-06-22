from fastapi import APIRouter, Query
from services.linkedin_client import linkedin

router = APIRouter(prefix="/posts", tags=["Post APIs"])

@router.get("/search", summary="Search Posts by keyword")
async def search_posts(keywords: str = Query(...), start: int = 0):
    return await linkedin.get("/search-posts", params={"keywords": keywords, "start": start})

@router.get("/by-hashtag", summary="Search Posts by Hashtag")
async def search_by_hashtag(hashtag: str = Query(..., description="Without #"), start: int = 0):
    return await linkedin.get("/search-post-by-hashtag", params={"hashtag": hashtag, "start": start})

@router.get("/", summary="Get Post by URN")
async def get_post(urn: str = Query(...)):
    return await linkedin.get("/get-post", params={"urn": urn})

@router.get("/reposts", summary="Get Post Reposts")
async def get_reposts(urn: str = Query(...), start: int = 0):
    return await linkedin.get("/get-post-reposts", params={"urn": urn, "start": start})
