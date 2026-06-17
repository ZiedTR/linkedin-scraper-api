from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
import logging

from routes import profile, company, jobs, posts, articles
from services.linkedin_client import linkedin

logging.basicConfig(level=logging.INFO)

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
        await linkedin.close()

        app = FastAPI(
            title="LinkedIn Scraper API - Enhanced",
                description="Real-Time LinkedIn Scraper API with caching, rate limiting, retry and Prometheus monitoring",
                    version="2.0.0",
                        lifespan=lifespan,
                            docs_url="/docs",
                                redoc_url="/redoc",
                                )

                                app.add_middleware(
                                    CORSMiddleware,
                                        allow_origins=["*"],
                                            allow_methods=["*"],
                                                allow_headers=["*"],
                                                )

                                                app.state.limiter = limiter
                                                app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

                                                Instrumentator().instrument(app).expose(app)

                                                app.include_router(profile.router)
                                                app.include_router(company.router)
                                                app.include_router(jobs.router)
                                                app.include_router(posts.router)
                                                app.include_router(articles.router)

                                                @app.get("/health", tags=["System"])
                                                async def health():
                                                    return {"status": "ok", "version": "2.0.0"}

                                                    @app.exception_handler(ValueError)
                                                    async def value_error_handler(request: Request, exc: ValueError):
                                                        return JSONResponse(status_code=400, content={"success": False, "message": str(exc)})

                                                        @app.exception_handler(RuntimeError)
                                                        async def runtime_error_handler(request: Request, exc: RuntimeError):
                                                            return JSONResponse(status_code=503, content={"success": False, "message": str(exc)})
                                                            
