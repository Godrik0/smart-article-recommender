from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecommendCreateRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "query": "I want to learn about deploying Python apps with Docker",
                "top_k": 5,
            }
        },
    )

    query: str = Field(
        min_length=2,
        max_length=1200,
        description="Natural language query describing what you want to learn.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of article recommendations to return (1-10).",
    )


class RecommendAcceptedResponse(BaseModel):
    request_id: str = Field(
        description="Unique identifier for the recommendation request.",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    task_id: str = Field(
        description="Celery task identifier for tracking progress.",
        examples=["c8e9f0a1-2b3c-4d5e-6f7a-8b9c0d1e2f3a"],
    )
    status: str = Field(
        description="Current request status: pending, running, completed, failed.",
        examples=["pending"],
    )


class ArticleResponse(BaseModel):
    id: int = Field(description="Unique article identifier.", examples=[1])
    title: str = Field(
        description="Article title.", examples=["Introduction to Docker"]
    )
    description: str = Field(
        description="Short article description or abstract.",
        examples=["A beginner-friendly guide to containerization."],
    )
    category: str = Field(
        description="Article category (e.g. Machine Learning, Systems).",
        examples=["DevOps"],
    )
    tags: list[str] = Field(
        description="List of topic tags associated with the article.",
        examples=[["docker", "containers"]],
    )
    url: str = Field(
        description="URL to the original article.",
        examples=["https://example.com/docker-intro"],
    )

    model_config = ConfigDict(from_attributes=True)


class RecommendedArticle(BaseModel):
    id: int = Field(description="Unique article identifier.", examples=[1])
    title: str = Field(
        description="Article title.", examples=["Introduction to Docker"]
    )
    description: str = Field(
        description="Short article description or abstract.",
        examples=["A beginner-friendly guide to containerization."],
    )
    category: str = Field(description="Article category.", examples=["DevOps"])
    tags: list[str] = Field(
        description="List of topic tags.", examples=[["docker", "containers"]]
    )
    url: str = Field(
        description="URL to the original article.",
        examples=["https://example.com/docker-intro"],
    )
    score: float = Field(
        description="Cosine similarity score between 0.0 and 1.0. Higher means more relevant.",
        ge=0.0,
        le=1.0,
        examples=[0.87],
    )


class RecommendResult(BaseModel):
    items: list[RecommendedArticle] = Field(
        description="Ordered list of recommended articles with similarity scores.",
        examples=[],
    )


class RecommendRequestResponse(BaseModel):
    id: str = Field(
        description="Unique request identifier (UUID).",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    query: str = Field(
        description="The user's original query text.",
        examples=["I want to learn about Docker"],
    )
    top_k: int = Field(description="Number of requested recommendations.", examples=[5])
    status: str = Field(
        description="Request status: pending, running, completed, failed.",
        examples=["completed"],
    )
    result: RecommendResult | None = Field(
        default=None,
        description="Recommendation results (present when status is completed).",
    )
    error: str | None = Field(
        default=None,
        description="Error message if the request failed.",
        examples=["Model not initialized"],
    )
    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when the request was created (ISO 8601).",
        examples=["2025-01-15T10:30:00Z"],
    )

    model_config = ConfigDict(from_attributes=True)


class RecommendListResponse(BaseModel):
    items: list[RecommendRequestResponse] = Field(
        description="List of recommendation requests, ordered by creation time descending.",
        examples=[],
    )


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse] = Field(
        description="List of articles matching the filter criteria.",
        examples=[],
    )


class HealthResponse(BaseModel):
    status: str = Field(
        description="Overall health status: ok or error.",
        examples=["ok"],
    )
    db: str = Field(
        description="Database connection status: ok or down.",
        examples=["ok"],
    )
    redis: str = Field(
        description="Redis connection status: ok or down.",
        examples=["ok"],
    )
    model: str = Field(
        description="ML model readiness status: ok or not_ready.",
        examples=["ok"],
    )


class ErrorResponse(BaseModel):
    detail: str = Field(
        description="Human-readable error description.",
        examples=["Task queue is temporarily unavailable"],
    )
