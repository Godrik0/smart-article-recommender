from __future__ import annotations

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class BadRequestError(Exception):
    pass


class ModelExecutionError(Exception):
    pass


async def bad_request_handler(_: Request, exc: BadRequestError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


async def validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": f"Invalid request payload: {exc.errors()}"},
    )


async def model_error_handler(_: Request, exc: ModelExecutionError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
