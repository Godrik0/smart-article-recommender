import pytest
import json
from unittest.mock import patch, MagicMock

from app.api import _parse_result_json


class TestParseResultJson:
    def test_none_returns_empty(self):
        assert _parse_result_json(None) == []

    def test_empty_string_returns_empty(self):
        assert _parse_result_json("") == []

    def test_valid_json_with_items(self):
        raw = json.dumps({"items": [{"article_id": 1, "score": 0.9}]})
        result = _parse_result_json(raw)
        assert len(result) == 1
        assert result[0]["article_id"] == 1

    def test_json_without_items_key(self):
        raw = json.dumps({"other": "data"})
        assert _parse_result_json(raw) == []

    def test_invalid_json_returns_empty(self):
        assert _parse_result_json("not json") == []


class TestApiEndpoints:
    @pytest.mark.asyncio
    async def test_articles_empty(self, client):
        resp = await client.get("/api/v1/articles")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_recommend_invalid_query(self, client):
        resp = await client.post("/api/v1/recommend", json={"query": "a"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_recommend_missing_body(self, client):
        resp = await client.post("/api/v1/recommend")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_recommend_valid(self, client, db_session):
        from app.models import Article

        article = Article(
            title="Test Article",
            description="A test article about Python.",
            category="Python",
            tags='["python"]',
            url="https://example.com/test",
        )
        db_session.add(article)
        await db_session.commit()

        mock_task = MagicMock()
        mock_task.id = "fake-task-id"

        with patch("app.api.celery_app") as mock_celery:
            mock_celery.send_task.return_value = mock_task
            resp = await client.post(
                "/api/v1/recommend",
                json={"query": "learn Python programming", "top_k": 3},
            )

        assert resp.status_code == 202
        data = resp.json()
        assert "request_id" in data
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_recommendation_not_found(self, client):
        resp = await client.get("/api/v1/recommend/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_articles_with_category(self, client, db_session):
        from app.models import Article

        db_session.add(
            Article(
                title="Py1",
                description="D",
                category="Python",
                tags='["py"]',
                url="https://example.com/1",
            )
        )
        db_session.add(
            Article(
                title="Go1",
                description="D",
                category="Go",
                tags='["go"]',
                url="https://example.com/2",
            )
        )
        await db_session.commit()

        resp = await client.get("/api/v1/articles?category=Python")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["category"] == "Python"

    @pytest.mark.asyncio
    async def test_list_recommendations_empty(self, client):
        resp = await client.get("/api/v1/recommend")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_recommend_queue_unavailable(self, client, db_session):
        with patch("app.api.celery_app") as mock_celery:
            mock_celery.send_task.side_effect = Exception("connection refused")
            resp = await client.post(
                "/api/v1/recommend",
                json={"query": "test query here", "top_k": 5},
            )
        assert resp.status_code == 503
