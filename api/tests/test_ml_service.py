import sys
from unittest.mock import MagicMock

sys.modules["sentence_transformers"] = MagicMock()  # noqa: E402

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from app.ml_service import RecommendationService  # noqa: E402
from app.errors import BadRequestError, ModelExecutionError  # noqa: E402


class TestRecommendationServiceNotReady:
    def test_is_ready_false_before_warmup(self):
        svc = RecommendationService(
            model_id="test", model_cache_dir="/tmp", model_device="cpu"
        )
        assert svc.is_ready is False

    def test_recommend_raises_when_not_ready(self):
        svc = RecommendationService(
            model_id="test", model_cache_dir="/tmp", model_device="cpu"
        )
        with pytest.raises(ModelExecutionError, match="not initialized"):
            svc.recommend("test query")

    def test_recommend_raises_on_empty_query(self):
        svc = RecommendationService(
            model_id="test", model_cache_dir="/tmp", model_device="cpu"
        )
        svc._ready = True
        svc._model = MagicMock()
        with pytest.raises(BadRequestError, match="must not be empty"):
            svc.recommend("   ")

    def test_recommend_raises_when_no_articles(self):
        svc = RecommendationService(
            model_id="test", model_cache_dir="/tmp", model_device="cpu"
        )
        svc._ready = True
        svc._model = MagicMock()
        svc._article_embeddings = None
        svc._article_ids = []
        with pytest.raises(ModelExecutionError, match="No articles"):
            svc.recommend("test query")


class TestRecommendationServiceRecommend:
    def test_recommend_returns_top_k(self, tmp_path):
        svc = RecommendationService(
            model_id="test",
            model_cache_dir="/tmp",
            model_device="cpu",
            embeddings_path=str(tmp_path / "emb.npz"),
        )
        svc._ready = True
        svc._article_ids = [1, 2, 3]
        svc._article_embeddings = np.array(
            [[0.9, 0.1], [0.1, 0.9], [0.5, 0.5]], dtype=np.float32
        )

        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.9, 0.1]], dtype=np.float32)
        svc._model = mock_model

        results = svc.recommend("docker containers", top_k=2)
        assert len(results) == 2
        assert results[0]["article_id"] == 1
        assert results[0]["score"] > results[1]["score"]

    def test_recommend_ranking(self, tmp_path):
        svc = RecommendationService(
            model_id="test",
            model_cache_dir="/tmp",
            model_device="cpu",
            embeddings_path=str(tmp_path / "emb.npz"),
        )
        svc._ready = True
        svc._article_ids = [10, 20, 30]
        svc._article_embeddings = np.array(
            [
                [1.0, 0.0],
                [0.0, 1.0],
                [0.5, 0.5],
            ],
            dtype=np.float32,
        )

        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.0, 1.0]], dtype=np.float32)
        svc._model = mock_model

        results = svc.recommend("test", top_k=3)
        assert results[0]["article_id"] == 20
