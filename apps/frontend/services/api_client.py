import logging
import requests
from typing import Dict, Any, Optional

from utils.config import settings

logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self):
        self.base_url = settings.BACKEND_URL.rstrip("/")
        self.timeout = 60  # generous timeout for agent operations

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e.response.text}")
            raise Exception(f"API Error: {e.response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise Exception(
                f"Connection Error: Could not reach backend at {self.base_url}"
            )

    def health(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return self._handle_response(response)
        except Exception:
            return {"status": "offline"}

    def upload_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        files = {"file": (filename, file_content, "application/pdf")}
        response = requests.post(
            f"{self.base_url}/api/v1/upload", files=files, timeout=self.timeout
        )
        return self._handle_response(response)

    def index_github(self, repository: str) -> Dict[str, Any]:
        payload = {"repository": repository}
        response = requests.post(
            f"{self.base_url}/api/v1/github/index", json=payload, timeout=self.timeout
        )
        return self._handle_response(response)

    def chat(
        self, question: str, session_id: str, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "question": question,
            "session_id": session_id,
            "conversation_id": conversation_id,
        }
        response = requests.post(
            f"{self.base_url}/api/v1/chat", json=payload, timeout=self.timeout
        )
        return self._handle_response(response)

    def agent_chat(
        self, question: str, session_id: str, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "question": question,
            "session_id": session_id,
            "conversation_id": conversation_id,
        }
        response = requests.post(
            f"{self.base_url}/api/v1/agent/chat", json=payload, timeout=self.timeout
        )
        return self._handle_response(response)

    def get_sessions(self, user_id: str = "default_user") -> list:
        response = requests.get(
            f"{self.base_url}/api/v1/memory/sessions",
            params={"user_id": user_id},
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def get_conversations(self, session_id: str) -> list:
        response = requests.get(
            f"{self.base_url}/api/v1/memory/conversations",
            params={"session_id": session_id},
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/v1/memory/conversation/{conversation_id}",
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def delete_conversation(self, conversation_id: str) -> Dict[str, Any]:
        response = requests.delete(
            f"{self.base_url}/api/v1/memory/conversation/{conversation_id}",
            timeout=self.timeout,
        )
        return self._handle_response(response)


api_client = APIClient()
