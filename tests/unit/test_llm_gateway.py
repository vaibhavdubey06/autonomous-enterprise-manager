import pytest
from app.services.llm.gateway import LLMGateway
from app.services.llm.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMProviderError,
    LLMTimeoutError,
    LLMError,
)
from google.api_core import exceptions as google_exceptions


def test_llm_service_gemini(mocker):
    mocker.patch(
        "app.services.llm.providers.gemini.settings.GEMINI_API_KEY", "test_key"
    )

    mock_genai = mocker.patch("app.services.llm.providers.gemini.genai.GenerativeModel")
    mock_instance = mocker.MagicMock()
    mock_genai.return_value = mock_instance

    mock_response = mocker.MagicMock()
    mock_response.text = "Mocked Gemini response"
    mock_instance.generate_content.return_value = mock_response

    service = LLMGateway()

    answer = service.generate_answer("What is AI?", ["context 1"])
    assert answer == "Mocked Gemini response"


def test_llm_service_exceptions(mocker):
    mocker.patch(
        "app.services.llm.providers.gemini.settings.GEMINI_API_KEY", "test_key"
    )
    mock_genai = mocker.patch("app.services.llm.providers.gemini.genai.GenerativeModel")
    mock_instance = mocker.MagicMock()
    mock_genai.return_value = mock_instance

    service = LLMGateway()

    # Avoid waiting for retries by setting retry_count to 1

    mock_instance.generate_content.side_effect = google_exceptions.PermissionDenied(
        "test"
    )
    with pytest.raises(LLMAuthenticationError):
        service.generate_answer("test question", [], retry_count=1)

    mock_instance.generate_content.side_effect = google_exceptions.ResourceExhausted(
        "test"
    )
    with pytest.raises(LLMRateLimitError):
        service.generate_answer("test question", [], retry_count=1)

    mock_instance.generate_content.side_effect = google_exceptions.ServiceUnavailable(
        "test"
    )
    with pytest.raises(LLMProviderError):
        service.generate_answer("test question", [], retry_count=1)

    mock_instance.generate_content.side_effect = google_exceptions.DeadlineExceeded(
        "test"
    )
    with pytest.raises(LLMTimeoutError):
        service.generate_answer("test question", [], retry_count=1)

    mock_instance.generate_content.side_effect = Exception("test")
    with pytest.raises(LLMError):
        service.generate_answer("test question", [], retry_count=1)

    # Test initialization error
    mock_genai.side_effect = Exception("test init")
    with pytest.raises(LLMProviderError):
        service.generate_answer("test question", [], retry_count=1)


def test_llm_service_empty_response(mocker):
    mocker.patch(
        "app.services.llm.providers.gemini.settings.GEMINI_API_KEY", "test_key"
    )
    mock_genai = mocker.patch("app.services.llm.providers.gemini.genai.GenerativeModel")
    mock_instance = mocker.MagicMock()
    mock_genai.return_value = mock_instance

    mock_response = mocker.MagicMock()
    mock_response.text = ""
    mock_instance.generate_content.return_value = mock_response

    service = LLMGateway()
    with pytest.raises(LLMProviderError):
        service.generate_answer("test question", [], retry_count=1)


def test_llm_service_no_api_key(mocker):
    mocker.patch("app.services.llm.providers.gemini.settings.GEMINI_API_KEY", "")
    service = LLMGateway()

    mock_genai = mocker.patch("app.services.llm.providers.gemini.genai.GenerativeModel")
    mock_genai.side_effect = Exception("test no api key")

    with pytest.raises(LLMProviderError):
        service.generate_answer("test question", [], retry_count=1)
