import pytest
from app.errors import BadRequestError, ModelExecutionError
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.errors import (
    bad_request_handler,
    validation_error_handler,
    model_error_handler,
    unhandled_error_handler,
)
from fastapi import Request


def _make_request() -> Request:
    req = Request(scope={"type": "http", "method": "GET", "path": "/", "headers": []})
    return req


class TestBadRequestHandler:
    @pytest.mark.asyncio
    async def test_returns_400(self):
        req = _make_request()
        resp = await bad_request_handler(req, BadRequestError("invalid data"))
        assert isinstance(resp, JSONResponse)
        assert resp.status_code == 400


class TestValidationErrorHandler:
    @pytest.mark.asyncio
    async def test_returns_422(self):
        req = _make_request()
        exc = RequestValidationError(
            errors=[
                {
                    "loc": ("body", "query"),
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        )
        resp = await validation_error_handler(req, exc)
        assert isinstance(resp, JSONResponse)
        assert resp.status_code == 422


class TestModelErrorHandler:
    @pytest.mark.asyncio
    async def test_returns_503(self):
        req = _make_request()
        resp = await model_error_handler(req, ModelExecutionError("model down"))
        assert isinstance(resp, JSONResponse)
        assert resp.status_code == 503


class TestUnhandledErrorHandler:
    @pytest.mark.asyncio
    async def test_returns_500(self):
        req = _make_request()
        resp = await unhandled_error_handler(req, RuntimeError("boom"))
        assert isinstance(resp, JSONResponse)
        assert resp.status_code == 500
