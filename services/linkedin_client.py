import httpx
import asyncio
from typing import Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "x-rapidapi-key": settings.rapidapi_key,
    "x-rapidapi-host": settings.rapidapi_host,
    "Content-Type": "application/json",
}

class LinkedInClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.base_url,
            headers=HEADERS,
            timeout=30.0,
        )

    async def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        for attempt in range(3):
            try:
                resp = await self.client.get(endpoint, params=params)
                resp.raise_for_status()
                data = resp.json()
                if not data.get("success", True):
                    raise ValueError(data.get("message", "API returned failure"))
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait}s (attempt {attempt+1}/3)")
                    await asyncio.sleep(wait)
                    continue
                raise RuntimeError(f"HTTP error {e.response.status_code}: {e.response.text}")
            except httpx.TimeoutException:
                if attempt == 2:
                    raise RuntimeError("Request timed out after 3 attempts")
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError("Max retries exceeded")

    async def close(self):
        await self.client.aclose()

linkedin = LinkedInClient()
