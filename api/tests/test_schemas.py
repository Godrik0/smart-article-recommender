from app.schemas import (
    RecommendCreateRequest,
    ArticleResponse,
    RecommendedArticle,
    HealthResponse,
    ErrorResponse,
)
from pydantic import ValidationError
import pytest


class TestRecommendCreateRequest:
    def test_valid(self):
        r = RecommendCreateRequest(query="docker containers", top_k=5)
        assert r.query == "docker containers"
        assert r.top_k == 5

    def test_default_top_k(self):
        r = RecommendCreateRequest(query="machine learning")
        assert r.top_k == 5

    def test_query_too_short(self):
        with pytest.raises(ValidationError):
            RecommendCreateRequest(query="a", top_k=5)

    def test_query_too_long(self):
        with pytest.raises(ValidationError):
            RecommendCreateRequest(query="x" * 1201, top_k=5)

    def test_top_k_below_min(self):
        with pytest.raises(ValidationError):
            RecommendCreateRequest(query="test query", top_k=0)

    def test_top_k_above_max(self):
        with pytest.raises(ValidationError):
            RecommendCreateRequest(query="test query", top_k=11)

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            RecommendCreateRequest(query="test", top_k=5, extra="bad")


class TestArticleResponse:
    def test_from_attributes(self):
        class FakeArticle:
            id = 1
            title = "Test"
            description = "Desc"
            category = "AI"
            tags = ["tag1"]
            url = "https://example.com"

        r = ArticleResponse.model_validate(FakeArticle(), from_attributes=True)
        assert r.id == 1
        assert r.title == "Test"
        assert r.tags == ["tag1"]


class TestRecommendedArticle:
    def test_score_validation(self):
        RecommendedArticle(
            id=1,
            title="T",
            description="D",
            category="C",
            tags=["t"],
            url="https://example.com",
            score=0.5,
        )

    def test_score_out_of_range(self):
        with pytest.raises(ValidationError):
            RecommendedArticle(
                id=1,
                title="T",
                description="D",
                category="C",
                tags=["t"],
                url="https://example.com",
                score=1.5,
            )


class TestHealthResponse:
    def test_ok(self):
        r = HealthResponse(status="ok", db="ok", redis="ok", model="ok")
        assert r.status == "ok"

    def test_model_not_ready(self):
        r = HealthResponse(status="ok", db="ok", redis="ok", model="not_ready")
        assert r.model == "not_ready"


class TestErrorResponse:
    def test_detail(self):
        r = ErrorResponse(detail="Something broke")
        assert r.detail == "Something broke"
