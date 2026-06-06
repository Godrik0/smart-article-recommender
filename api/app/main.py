from __future__ import annotations

import logging
import signal
import time
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from .api import router
from .config import get_settings
from .db import SessionLocal, engine
from .errors import (
    BadRequestError,
    ModelExecutionError,
    bad_request_handler,
    model_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from .logging_setup import setup_logging

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    app.state.shutting_down = False

    logger.info("Initializing Redis connection: %s", settings.redis_url)
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    await app.state.redis.ping()
    logger.info("Redis connection established")

    logger.info("Verifying database connectivity")
    async with SessionLocal() as session:
        await session.execute(text("SELECT 1"))
    logger.info("Database connection verified")

    def _graceful_term(*_: object) -> None:
        logger.info("SIGTERM received, marking service for shutdown")
        app.state.shutting_down = True

    signal.signal(signal.SIGTERM, _graceful_term)
    logger.info("Application startup complete")
    yield

    logger.info("Shutting down application")
    app.state.shutting_down = True
    await app.state.redis.close()
    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
app.include_router(router, prefix=settings.api_prefix)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(BadRequestError, bad_request_handler)
app.add_exception_handler(ModelExecutionError, model_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.middleware("http")
async def reject_when_shutting_down(request: Request, call_next):
    if app.state.shutting_down and request.url.path != "/health":
        return JSONResponse(
            status_code=503, content={"detail": "Service is shutting down"}
        )
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    logger.info(
        "method=%s path=%s status=%d duration_sec=%.4f",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


@app.get("/health")
async def root_health(request: Request):
    db_status = "ok"
    redis_status = "ok"
    model_status = "not_ready"
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"
        logger.warning("Health check: database is down")
    try:
        await request.app.state.redis.ping()
        model_ready_val = await request.app.state.redis.get("model:ready")
        if model_ready_val == "1":
            model_status = "ok"
    except Exception:
        redis_status = "down"
        logger.warning("Health check: redis is down")
    if db_status != "ok" or redis_status != "ok":
        raise HTTPException(status_code=503, detail="Dependencies are not ready")
    return {
        "status": "ok",
        "db": db_status,
        "redis": redis_status,
        "model": model_status,
    }
