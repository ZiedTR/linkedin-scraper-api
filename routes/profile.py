from fastapi import APIRouter, Query
from services.linkedin_client import linkedin
from typing import Optional

router = APIRouter(prefix="/profile", tags=["Profile APIs"])

@router.get("/", summary="Get Profile Data")
async def get_profile(username: str = Query(..., description="LinkedIn username")):
    return await linkedin.get("/", params={"username": username})

    @router.get("/by-url", summary="Get Profile Data By URL")
    async def get_profile_by_url(url: str = Query(...)):
        return await linkedin.get("/get-profile-data-by-url", params={"url": url})

        @router.get("/search", summary="Search People")
        async def search_people(
            keywords: Optional[str] = None,
                start: int = 0,
                    geo: Optional[str] = None,
                        firstName: Optional[str] = None,
                            lastName: Optional[str] = None,
                                keywordTitle: Optional[str] = None,
                                    company: Optional[str] = None,
                                    ):
                                        params = {k: v for k, v in locals().items() if v is not None}
                                            return await linkedin.get("/search-people", params=params)

                                            @router.get("/activity-time", summary="Get Profile Recent Activity Time")
                                            async def get_activity_time(username: str = Query(...)):
                                                return await linkedin.get("/get-profile-recent-activity-time", params={"username": username})

                                                @router.get("/posts", summary="Get Profile Posts")
                                                async def get_profile_posts(username: str = Query(...), start: int = 0):
                                                    return await linkedin.get("/get-profile-posts", params={"username": username, "start": start})

                                                    @router.get("/connections", summary="Get Connection and Follower Count")
                                                    async def get_connections(username: str = Query(...)):
                                                        return await linkedin.get("/get-profile-connections", params={"username": username})

                                                        @router.get("/recommendations/received", summary="Get Received Recommendations")
                                                        async def get_received_recommendations(username: str = Query(...)):
                                                            return await linkedin.get("/get-received-recommendations", params={"username": username})

                                                            @router.get("/recommendations/given", summary="Get Given Recommendations")
                                                            async def get_given_recommendations(username: str = Query(...)):
                                                                return await linkedin.get("/get-given-recommendations", params={"username": username})

                                                                @router.get("/reactions", summary="Get Profile Reactions")
                                                                async def get_reactions(username: str = Query(...), start: int = 0):
                                                                    return await linkedin.get("/get-profile-reactions", params={"username": username, "start": start})

                                                                    @router.get("/about", summary="About The Profile")
                                                                    async def about_profile(username: str = Query(...)):
                                                                        return await linkedin.get("/get-about-profile", params={"username": username})

                                                                        @router.get("/similar", summary="Get Similar Profiles")
                                                                        async def get_similar(username: str = Query(...)):
                                                                            return await linkedin.get("/get-similar-profiles", params={"username": username})
                                                                            
