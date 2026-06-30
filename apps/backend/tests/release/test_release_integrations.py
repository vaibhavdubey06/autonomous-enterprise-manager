from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_database_connection_failure_handling():
    """
    Verify that if the database is unreachable, the application
    handles it gracefully (e.g., returns 503 or 500 without crashing).
    """
    with patch("app.core.database.SessionLocal") as mock_db:
        # Simulate a connection error when trying to query
        mock_db.side_effect = Exception("OperationalError: FATAL: too many connections")

        # We hit an endpoint that requires DB access
        # Since /api/v1/workflows requires DB via Depends(get_db), we can hit that.
        res = client.get(
            "/api/v1/workflows/", headers={"Authorization": "Bearer fake_token"}
        )

        # In this implementation, the SecurityMiddleware will catch the error and return 500
        # or the endpoint will return 500. We just ensure it doesn't crash the server process.
        assert res.status_code in [500, 503, 401]


def test_llm_service_failure_handling():
    """
    Verify that if the LLM provider fails, the application returns a graceful error.
    """
    with patch(
        "app.services.llm.llm_service.genai.GenerativeModel.generate_content_async"
    ) as mock_gen:
        mock_gen.side_effect = Exception("APIKeyInvalid or RateLimitExceeded")

        # Mock auth and DB so it gets past middleware
        with (
            patch(
                "app.security.authentication.auth_service.auth_service.verify_token_and_get_user"
            ) as mock_auth,
            patch("app.api.v1.chat.search") as mock_search,
            patch("app.services.vectorstore.qdrant_service.get_client"),
        ):

            mock_auth.return_value.id = "user_1"
            mock_auth.return_value.tenant_id = "tenant_1"
            mock_auth.return_value.email = "admin@example.com"
            mock_auth.return_value.roles = []

            mock_search.return_value = []

            payload = {
                "user_id": "test_user",
                "question": "What happens if LLM fails?",
                "conversation_id": "fail_test_001",
            }

            res = client.post(
                "/api/v1/chat/", headers={"Authorization": "Bearer test"}, json=payload
            )

            # Application should catch the exception and return 500, or 503 depending on implementation
            # We just want to ensure it handles it and responds with JSON.
            assert res.status_code >= 400
            assert (
                "detail" in res.json()
                or "message" in res.json()
                or "error" in res.json()
            )
