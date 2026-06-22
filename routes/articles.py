from fastapi import APIRouter, Query
from services.linkedin_client import linkedin

router = APIRouter(prefix="/articles", tags=["Article API"])

@router.get("/by-user", summary="Get User Articles")
async def get_user_articles(username: str = Query(...)):
    return await linkedin.get("/get-user-articles", params={"username": username})

@router.get("/", summary="Get Article")
async def get_article(url: str = Query(...)):
    return await linkedin.get("/get-article", params={"url": url})

@router.get("/comments", summary="Get Article Comments")
async def get_article_comments(url: str = Query(...), start: int = 0):
    return await linkedin.get("/get-article-comments", params={"url": url, "start": start})

@router.get("/reactions", summary="Get Article Reactions")
async def get_article_reactions(url: str = Query(...)):
    return await linkedin.get("/get-article-reactions", params={"url": url})
