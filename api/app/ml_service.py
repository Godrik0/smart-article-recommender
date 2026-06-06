from __future__ import annotations

import logging
import threading
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from .errors import BadRequestError, ModelExecutionError
from .logging_setup import timed_step

logger = logging.getLogger(__name__)

EMBED_BATCH_SIZE = 256


class RecommendationService:
    def __init__(
        self,
        model_id: str,
        model_cache_dir: str,
        model_device: str,
        embeddings_path: str = "/models/article_embeddings.npz",
    ) -> None:
        self.model_id = model_id
        self.model_cache_dir = model_cache_dir
        self.model_device = model_device
        self._embeddings_path = Path(embeddings_path)
        self._model: SentenceTransformer | None = None
        self._article_embeddings: np.ndarray | None = None
        self._article_ids: list[int] = []
        self._ready = False
        self._lock = threading.Lock()

    @property
    def is_ready(self) -> bool:
        return self._ready

    def warmup(self, articles: list[dict]) -> None:
        with timed_step(logger, "model_warmup"):
            self._model = SentenceTransformer(
                self.model_id,
                cache_folder=self.model_cache_dir,
                device=self.model_device,
            )

            if self._embeddings_path.exists():
                self._load_embeddings()
            elif articles:
                self._build_and_save_embeddings(articles)

            self._ready = True
            logger.info(
                "Recommendation model ready, %d articles indexed",
                len(self._article_ids),
            )

    def _load_embeddings(self) -> None:
        with timed_step(logger, "load_embeddings"):
            data = np.load(self._embeddings_path, allow_pickle=False)
            self._article_ids = data["ids"].tolist()
            self._article_embeddings = data["embeddings"]
        logger.info(
            "Loaded pre-computed embeddings for %d articles from %s",
            len(self._article_ids),
            self._embeddings_path,
        )

    def _build_and_save_embeddings(self, articles: list[dict]) -> None:
        self._article_ids = [a["id"] for a in articles]
        texts = [
            f"{a['title']}. {a['description']} {' '.join(a['tags'])}" for a in articles
        ]
        logger.info(
            "Computing embeddings for %d texts in batches of %d...",
            len(texts),
            EMBED_BATCH_SIZE,
        )

        with timed_step(logger, "compute_embeddings"):
            all_embeddings = []
            for i in range(0, len(texts), EMBED_BATCH_SIZE):
                batch = texts[i : i + EMBED_BATCH_SIZE]
                batch_emb = self._model.encode(
                    batch, normalize_embeddings=True, show_progress_bar=False
                )
                all_embeddings.append(batch_emb)
                logger.info(
                    "Encoded batch %d/%d",
                    i // EMBED_BATCH_SIZE + 1,
                    -(-len(texts) // EMBED_BATCH_SIZE),
                )

            self._article_embeddings = np.vstack(all_embeddings)

        self._embeddings_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            self._embeddings_path,
            ids=np.array(self._article_ids),
            embeddings=self._article_embeddings,
        )
        logger.info(
            "Saved embeddings for %d articles to %s",
            len(self._article_ids),
            self._embeddings_path,
        )

    def rebuild_index(self, articles: list[dict]) -> None:
        self._build_and_save_embeddings(articles)
        logger.info("Index rebuilt with %d articles", len(self._article_ids))

    def recommend(self, query: str, top_k: int = 5) -> list[dict]:
        if not self._ready or self._model is None:
            raise ModelExecutionError("Recommendation model is not initialized yet.")
        if not query.strip():
            raise BadRequestError("Query must not be empty.")
        if self._article_embeddings is None or len(self._article_ids) == 0:
            raise ModelExecutionError("No articles available for recommendation.")

        with self._lock:
            with timed_step(logger, "recommend"):
                query_embedding = self._model.encode(
                    [query], normalize_embeddings=True, show_progress_bar=False
                )
                scores = np.dot(self._article_embeddings, query_embedding.T).flatten()
                top_indices = np.argsort(scores)[::-1][:top_k]
                results = []
                for idx in top_indices:
                    results.append(
                        {
                            "article_id": int(self._article_ids[idx]),
                            "score": float(scores[idx]),
                        }
                    )
                return results
