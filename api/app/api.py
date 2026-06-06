from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from .celery_app import celery_app
from .db import get_db_session
from .logging_setup import timed_step
from .models import Article, RecommendationRequest, RequestStatus
from .schemas import (
    ArticleListResponse,
    ArticleResponse,
    RecommendAcceptedResponse,
    RecommendCreateRequest,
    RecommendListResponse,
    RecommendRequestResponse,
    RecommendResult,
    RecommendedArticle,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def _resolve_articles(
    db: AsyncSession,
    requests_with_results: list[tuple[RecommendationRequest, list[dict]]],
) -> dict[str, RecommendResult]:
    if not requests_with_results:
        return {}

    all_article_ids: set[int] = set()
    for _, articles_data in requests_with_results:
        for a in articles_data:
            all_article_ids.add(a["article_id"])

    if not all_article_ids:
        return {}

    rows = await db.execute(select(Article).where(Article.id.in_(all_article_ids)))
    article_map = {a.id: a for a in rows.scalars().all()}

    results: dict[str, RecommendResult] = {}
    for req, articles_data in requests_with_results:
        score_map = {a["article_id"]: a["score"] for a in articles_data}
        items = []
        for a in articles_data:
            article = article_map.get(a["article_id"])
            if article:
                items.append(
                    RecommendedArticle(
                        id=article.id,
                        title=article.title,
                        description=article.description,
                        category=article.category,
                        tags=json.loads(article.tags),
                        url=article.url,
                        score=score_map[a["article_id"]],
                    )
                )
        results[req.id] = RecommendResult(items=items)

    return results


def _parse_result_json(raw: str | None) -> list[dict]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        return parsed.get("items", [])
    except (json.JSONDecodeError, AttributeError):
        return []


@router.post(
    "/recommend",
    response_model=RecommendAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_recommendation(
    payload: RecommendCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> RecommendAcceptedResponse:
    logger.info(
        "Recommendation request received: query=%r top_k=%d",
        payload.query[:80],
        payload.top_k,
    )

    req = RecommendationRequest(
        query=payload.query,
        top_k=payload.top_k,
        status=RequestStatus.pending.value,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)

    try:
        with timed_step(logger, "dispatch_task"):
            task = celery_app.send_task(
                "app.tasks.recommend_task",
                args=[req.id, payload.query, payload.top_k],
            )
    except Exception as exc:
        req.status = RequestStatus.failed.value
        req.error = f"Queue is unavailable: {exc}"
        await db.commit()
        logger.error("Failed to dispatch task for request %s: %s", req.id, exc)
        raise HTTPException(
            status_code=503, detail="Task queue is temporarily unavailable"
        ) from exc

    req.celery_task_id = task.id
    await db.commit()
    logger.info("Task %s dispatched for request %s", task.id, req.id)

    return RecommendAcceptedResponse(
        request_id=req.id, task_id=task.id, status=req.status
    )


@router.get("/recommend/{request_id}", response_model=RecommendRequestResponse)
async def get_recommendation(
    request_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> RecommendRequestResponse:
    req = await db.get(RecommendationRequest, request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Recommendation request not found")

    result = None
    articles_data = _parse_result_json(req.result)
    if articles_data:
        resolved = await _resolve_articles(db, [(req, articles_data)])
        result = resolved.get(req.id)

    if req.status in (RequestStatus.completed.value, RequestStatus.failed.value):
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_202_ACCEPTED

    return RecommendRequestResponse(
        id=req.id,
        query=req.query,
        top_k=req.top_k,
        status=req.status,
        result=result,
        error=req.error,
        created_at=req.created_at,
    )


@router.get("/recommend", response_model=RecommendListResponse)
async def list_recommendations(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> RecommendListResponse:
    rows = await db.execute(
        select(RecommendationRequest)
        .order_by(desc(RecommendationRequest.created_at))
        .limit(limit)
    )
    requests = rows.scalars().all()

    to_resolve = []
    for req in requests:
        articles_data = _parse_result_json(req.result)
        if articles_data:
            to_resolve.append((req, articles_data))

    resolved_map = await _resolve_articles(db, to_resolve)

    items = []
    for req in requests:
        items.append(
            RecommendRequestResponse(
                id=req.id,
                query=req.query,
                top_k=req.top_k,
                status=req.status,
                result=resolved_map.get(req.id),
                error=req.error,
                created_at=req.created_at,
            )
        )
    return RecommendListResponse(items=items)


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    category: str | None = Query(default=None, description="Filter by category"),
    db: AsyncSession = Depends(get_db_session),
) -> ArticleListResponse:
    stmt = select(Article).order_by(Article.id)
    if category:
        stmt = stmt.where(Article.category == category)
    rows = await db.execute(stmt)
    articles = rows.scalars().all()
    items = [
        ArticleResponse(
            id=a.id,
            title=a.title,
            description=a.description,
            category=a.category,
            tags=json.loads(a.tags),
            url=a.url,
        )
        for a in articles
    ]
    return ArticleListResponse(items=items)
