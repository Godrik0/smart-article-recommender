import json

from app.models import Article, RecommendationRequest, RequestStatus


class TestArticleModel:
    def test_create(self):
        a = Article(
            title="Test",
            description="Desc",
            category="AI",
            tags='["ml"]',
            url="https://example.com",
        )
        assert a.title == "Test"
        assert a.category == "AI"

    def test_tags_stored_as_json_string(self):
        tags = ["python", "docker"]
        a = Article(
            title="T",
            description="D",
            category="C",
            tags=json.dumps(tags),
            url="https://example.com",
        )
        assert json.loads(a.tags) == ["python", "docker"]


class TestRecommendationRequestModel:
    def test_default_values(self):
        req = RecommendationRequest(
            query="test", top_k=5, status=RequestStatus.pending.value
        )
        assert req.status == RequestStatus.pending.value
        assert req.top_k == 5


class TestRequestStatus:
    def test_values(self):
        assert RequestStatus.pending == "pending"
        assert RequestStatus.running == "running"
        assert RequestStatus.completed == "completed"
        assert RequestStatus.failed == "failed"
