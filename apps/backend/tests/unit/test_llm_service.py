import pytest
from app.services.llm.llm_service import LLMService
from fastapi import HTTPException
from google.api_core import exceptions as google_exceptions


def test_llm_service_gemini(mocker):
    mocker.patch("app.services.llm.llm_service.settings.GEMINI_API_KEY", "test_key")

    mock_genai = mocker.patch("app.services.llm.llm_service.genai.GenerativeModel")
    mock_instance = mocker.MagicMock()
    mock_genai.return_value = mock_instance

    mock_response = mocker.MagicMock()
    mock_response.text = "Mocked Gemini response"
    mock_instance.generate_content.return_value = mock_response

    service = LLMService()

    answer = service.generate_answer("What is AI?", ["context 1"])
    assert answer == "Mocked Gemini response"


def test_llm_service_exceptions(mocker):
    mocker.patch("app.services.llm.llm_service.settings.GEMINI_API_KEY", "test_key")
    mock_genai = mocker.patch("app.services.llm.llm_service.genai.GenerativeModel")
    mock_instance = mocker.MagicMock()
    mock_genai.return_value = mock_instance

    service = LLMService()

    mock_instance.generate_content.side_effect = google_exceptions.PermissionDenied(
        "test"
    )
    with pytest.raises(HTTPException) as excinfo:
        service.generate_answer("test question", [])
    assert excinfo.value.status_code == 401

    mock_instance.generate_content.side_effect = google_exceptions.ResourceExhausted(
        "test"
    )
    with pytest.raises(HTTPException) as excinfo:
        service.generate_answer("test question", [])
    assert excinfo.value.status_code == 429

    mock_instance.generate_content.side_effect = google_exceptions.ServiceUnavailable(
        "test"
    )
    with pytest.raises(HTTPException) as excinfo:
        service.generate_answer("test question", [])
    assert excinfo.value.status_code == 503

    mock_instance.generate_content.side_effect = google_exceptions.DeadlineExceeded(
        "test"
    )
    with pytest.raises(HTTPException) as excinfo:
        service.generate_answer("test question", [])
    assert excinfo.value.status_code == 504

    mock_instance.generate_content.side_effect = Exception("test")
    with pytest.raises(HTTPException) as excinfo:
        service.generate_answer("test question", [])
    assert excinfo.value.status_code == 500

    # Test initialization error
    mock_genai.side_effect = Exception("test init")
    with pytest.raises(HTTPException) as excinfo:
        service.generate_answer("test question", [])
    assert excinfo.value.status_code == 500


def test_llm_service_empty_response(mocker):
    mocker.patch("app.services.llm.llm_service.settings.GEMINI_API_KEY", "test_key")
    mock_genai = mocker.patch("app.services.llm.llm_service.genai.GenerativeModel")
    mock_instance = mocker.MagicMock()
    mock_genai.return_value = mock_instance

    mock_response = mocker.MagicMock()
    mock_response.text = ""
    mock_instance.generate_content.return_value = mock_response

    service = LLMService()
    with pytest.raises(HTTPException) as excinfo:
        service.generate_answer("test question", [])
    assert excinfo.value.status_code == 500


def test_llm_service_no_api_key(mocker):
    mocker.patch("app.services.llm.llm_service.settings.GEMINI_API_KEY", "")
    service = LLMService()

    with pytest.raises(HTTPException) as excinfo:
        service.generate_answer("test question", [])
    assert excinfo.value.status_code == 500
