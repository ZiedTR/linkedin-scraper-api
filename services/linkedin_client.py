import asyncio
import logging
import time
from typing import Any, Optional
import httpx
from config import get_settings

logger = logging.getLogger("linkedin.client")
settings = get_settings()


class TTLCache:
    def __init__(self, maxsize: int, ttl: int):
        self.maxsize = maxsize
        self.ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}
        self._access_times: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key not in self._store:
                return None
            expires, value = self._store[key]
            if time.time() > expires:
                del self._store[key]
                self._access_times.pop(key, None)
                return None
            self._access_times[key] = time.time()
            return value

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            if len(self._store) >= self.maxsize:
                lru_key = min(self._access_times, key=self._access_times.get)
                del self._store[lru_key]
                del self._access_times[lru_key]
            self._store[key] = (time.time() + self.ttl, value)
            self._access_times[key] = time.time()


class LinkedInAPIError(RuntimeError):
    def __init__(self, message: str, status: int = 503):
        super().__init__(message)
        self.status = status


class LinkedInClient:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._cache = TTLCache(settings.cache_maxsize, settings.cache_ttl)
        self.metrics = {
            "requests": 0,
            "cache_hits": 0,
            "errors": 0,
            "retries": 0,
            "429_throttles": 0,
        }

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=settings.base_url,
                timeout=settings.request_timeout,
                headers={
                    "x-rapidapi-key": settings.rapidapi_key,
                    "x-rapidapi-host": settings.rapidapi_host,
                    "Content-Type": "application/json",
                },
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._client

    def _cache_key(self, method: str, path: str, params: dict | None, body: dict | None) -> str:
        params_str = str(sorted((params or {}).items()))
        body_str = str(sorted((body or {}).items()))
        return f"{method}:{path}:{params_str}:{body_str}"

    async def request(
        self,
        path: str,
        method: str = "GET",
        params: dict | None = None,
        json_body: dict | None = None,
        use_cache: bool = True,
    ) -> Any:
        key = self._cache_key(method, path, params, json_body)
        if use_cache and method == "GET":
            cached = await self._cache.get(key)
            if cached is not None:
                self.metrics["cache_hits"] += 1
                return cached

        last_exc: Exception | None = None
        for attempt in range(settings.max_retries):
            try:
                self.metrics["requests"] += 1
                resp = await self.client.request(method, path, params=params, json=json_body)

                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", settings.backoff_base * (2 ** attempt)))
                    self.metrics["retries"] += 1
                    self.metrics["429_throttles"] += 1
                    logger.warning("429 Throttled - waiting %.1fs", retry_after)
                    await asyncio.sleep(retry_after)
                    continue

                if resp.status_code >= 500:
                    self.metrics["retries"] += 1
                    wait_time = settings.backoff_base * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                    continue

                if resp.status_code == 404:
                    raise LinkedInAPIError("Resource not found", status=404)

                if resp.status_code == 401:
                    raise LinkedInAPIError("Authentication failed - check your RapidAPI key", status=401)

                resp.raise_for_status()
                data = resp.json()

                if use_cache and method == "GET":
                    await self._cache.set(key, data)

                return data

            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                self.metrics["retries"] += 1
                if attempt < settings.max_retries - 1:
                    await asyncio.sleep(settings.backoff_base * (2 ** attempt))

        self.metrics["errors"] += 1
        raise LinkedInAPIError(f"Request failed after {settings.max_retries} attempts", status=503)

    # Convenience methods used by routes
    async def get(self, path: str, params: dict | None = None, use_cache: bool = True) -> Any:
        return await self.request(path, method="GET", params=params, use_cache=use_cache)

    async def post(self, path: str, json_body: dict | None = None) -> Any:
        return await self.request(path, method="POST", json_body=json_body, use_cache=False)

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


linkedin = LinkedInClient()
