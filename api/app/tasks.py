from __future__ import annotations

import json
import logging
import signal

import redis as sync_redis
from celery.signals import worker_process_init, worker_process_shutdown
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from .celery_app import celery_app
from .config import get_settings
from .logging_setup import setup_logging, timed_step
from .ml_service import RecommendationService
from .models import Article, RecommendationRequest, RequestStatus

settings = get_settings()
logger = logging.getLogger(__name__)

sync_engine = create_engine(settings.database_sync_url, future=True)
SyncSession = sessionmaker(bind=sync_engine, expire_on_commit=False, class_=Session)

recommendation_service: RecommendationService | None = None
_shutting_down = False


def _sigterm_handler(signum: int, frame: object) -> None:
    global _shutting_down
    logger.info("Worker received SIGTERM, draining current tasks...")
    _shutting_down = True


signal.signal(signal.SIGTERM, _sigterm_handler)


@worker_process_init.connect
def on_worker_init(**kwargs):
    global recommendation_service
    setup_logging()

    recommendation_service = RecommendationService(
        model_id=settings.model_id,
        model_cache_dir=settings.model_cache_dir,
        model_device=settings.model_device,
    )

    with SyncSession() as session:
        articles = session.execute(select(Article)).scalars().all()
        article_dicts = [
            {
                "id": a.id,
                "title": a.title,
                "description": a.description,
                "tags": json.loads(a.tags),
            }
            for a in articles
        ]

    recommendation_service.warmup(article_dicts)
    r = sync_redis.from_url(settings.celery_result_backend, decode_responses=True)
    r.set("model:ready", "1")
    logger.info("Recommendation model loaded and model:ready flag set in Redis")


@worker_process_shutdown.connect
def on_worker_shutdown(**kwargs):
    try:
        r = sync_redis.from_url(settings.celery_result_backend, decode_responses=True)
        r.delete("model:ready")
        logger.info("model:ready flag cleared in Redis")
    except Exception:
        pass


@celery_app.task(name="app.tasks.recommend_task", bind=True)
def recommend_task(self, request_id: str, query: str, top_k: int) -> dict[str, str]:
    global recommendation_service, _shutting_down
    if _shutting_down:
        logger.warning("Rejecting task %s — worker is shutting down", self.request.id)
        return {
            "status": "rejected",
            "request_id": request_id,
            "error": "Worker shutting down",
        }
    if recommendation_service is None:
        return {
            "status": "error",
            "request_id": request_id,
            "error": "Model not initialized",
        }
    with SyncSession() as session:
        req = session.execute(
            select(RecommendationRequest).where(RecommendationRequest.id == request_id)
        ).scalar_one_or_none()
        if req is None:
            return {"status": "missing", "request_id": request_id}
        req.status = RequestStatus.running.value
        session.commit()
        try:
            with timed_step(logger, "worker_recommend"):
                recommendations = recommendation_service.recommend(
                    query=query, top_k=top_k
                )
            req.status = RequestStatus.completed.value
            req.result = json.dumps({"items": recommendations})
            req.error = None
            session.commit()
            return {"status": RequestStatus.completed.value, "request_id": request_id}
        except Exception as exc:
            logger.exception(
                "Task %s failed for request %s", self.request.id, request_id
            )
            req.status = RequestStatus.failed.value
            req.error = str(exc)
            session.commit()
            return {"status": RequestStatus.failed.value, "request_id": request_id}
