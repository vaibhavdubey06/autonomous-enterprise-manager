import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.core.database import Base, engine

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers():
    from app.security.authentication.jwt_provider import JWTProvider

    provider = JWTProvider()
    token = provider.create_access_token({"sub": "admin_user", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


def test_full_platform_e2e(auth_headers):
    """
    Validates End-to-End Enterprise Scenario.
    """
    chat_payload = {
        "user_id": "release_admin",
        "question": "We need to analyze our repository architecture.",
        "conversation_id": "release_e2e_001",
    }

    with (
        patch(
            "app.services.llm.providers.gemini.genai.GenerativeModel.generate_content_async"
        ) as mock_generate,
        patch("app.api.v1.chat.search") as mock_api_search,
        patch("app.services.chat_service.search") as mock_service_search,
        patch("app.services.memory_service.search") as mock_memory_search,
        patch("app.services.vectorstore.qdrant_service.get_client") as mock_get_client,
    ):

        mock_api_search.return_value = []
        mock_service_search.return_value = []
        mock_memory_search.return_value = []

        mock_client_instance = MagicMock()
        mock_client_instance.get_collections.return_value.collections = [
            MagicMock(name="enterprise_knowledge")
        ]
        mock_get_client.return_value = mock_client_instance

        mock_generate_obj = MagicMock()
        mock_generate_obj.text = "I have reviewed the architecture."
        mock_generate.return_value = mock_generate_obj

        response = client.post("/api/v1/chat/", headers=auth_headers, json=chat_payload)

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}. Detail: {response.text}"
        data = response.json()
        assert "answer" in data

        health_res = client.get("/health")
        assert health_res.status_code == 200
        assert health_res.json()["status"] == "healthy"
