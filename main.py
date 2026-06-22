from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
import logging
import sys

from config import get_settings
from routes import profile, company, jobs, posts, articles, location
from routes import ai, network, batch, webhooks
from services.linkedin_client import linkedin, LinkedInAPIError

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("linkedin_api")
settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])


@asynccontextmanager
async def lifespan(app: FastAPI):
        logger.info("=" * 60)
        logger.info("LinkedIn Pro API v4.0 STARTED")
        logger.info("Cache TTL: %ds | Retries: %d | Rate: %s", settings.cache_ttl, settings.max_retries, settings.rate_limit)
        logger.info("NEW: AI Scoring | Batch | Webhooks | Network Graph")
        logger.info("=" * 60)
        yield
        logger.info("Shutting down...")
        await linkedin.close()


app = FastAPI(
        title="LinkedIn Pro API - v4.0",
        description="""
## LinkedIn Data API with AI Enrichment

The only LinkedIn API with:
- **AI Influence Score** — score 0-100 per profile
- **Career Trajectory** — predict next job move
- **Sentiment Analysis** — tone of recent posts
- **Batch Enrichment** — 100 profiles in 1 request
- **Real-Time Webhooks** — alerts on job/headline changes
- **Network Graph** — proximity score, org chart reconstruction

Plus all classic endpoints: profiles, companies, jobs, posts, articles.
        """,
        version="4.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
)

app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
Instrumentator().instrument(app).expose(app)

for router in (profile, company, jobs, posts, articles, location,
               ai, network, batch, webhooks):
        app.include_router(router.router)


@app.get("/health", tags=["System"])
async def health():
        return {
                    "status": "healthy",
                    "version": "4.0.0",
                    "endpoints": {"total": 75, "get": 58, "post": 17},
                    "features": {
                                    "cache_enabled": True,
                                    "cache_ttl_seconds": settings.cache_ttl,
                                    "cache_strategy": "LRU with TTL",
                                    "retry_enabled": True,
                                    "max_retries": settings.max_retries,
                                    "ai_enrichment": True,
                                    "batch_processing": True,
                                    "webhooks": True,
                                    "network_graph": True,
                    },
                    "metrics": {
                                    "requests_total": linkedin.metrics["requests"],
                                    "cache_hits": linkedin.metrics["cache_hits"],
                                    "cache_hit_rate": f"{(linkedin.metrics['cache_hits'] / max(linkedin.metrics['requests'], 1)) * 100:.1f}%",
                                    "retries": linkedin.metrics["retries"],
                                    "throttle_429": linkedin.metrics["429_throttles"],
                                    "errors": linkedin.metrics["errors"],
                    },
        }


@app.exception_handler(LinkedInAPIError)
async def linkedin_error_handler(request: Request, exc: LinkedInAPIError):
        return JSONResponse(
                    status_code=exc.status,
                    content={"success": False, "message": str(exc), "error_type": "LinkedInAPIError"}
        )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": str(exc), "error_type": "ValueError"}
        )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
        logger.error("Unhandled error: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Internal server error", "error_type": "InternalServerError"}
        )


if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
