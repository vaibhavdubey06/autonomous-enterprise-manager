from abc import ABC, abstractmethod
from typing import List
import json
import logging
from app.services.memory.models import ExtractedMemory, MemoryExtractionResult
from app.services.llm.llm_service import LLMService

logger = logging.getLogger(__name__)


class MemoryExtractionStrategy(ABC):
    @abstractmethod
    def extract(
        self, history: str, user_message: str, assistant_response: str
    ) -> List[ExtractedMemory]:
        pass


class GeminiMemoryExtractionStrategy(MemoryExtractionStrategy):
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.strategy_name = "GeminiMemoryExtractionStrategy"
        self.version = "1.0"

    def extract(
        self, history: str, user_message: str, assistant_response: str
    ) -> List[ExtractedMemory]:
        prompt = (
            "You are a Memory Extraction Assistant.\n"
            "Analyze the following conversation and extract any long-term memories that would be useful for the future.\n"
            "Respond ONLY with a JSON object containing a 'memories' array.\n"
            "Return an empty array if there is no useful long-term information (e.g. greetings, small talk).\n"
            "Do NOT store greetings, small talk, acknowledgements, or generic assistant replies.\n\n"
            "Allowed memory types: FACT, DECISION, GOAL, PREFERENCE, PERSON, PROJECT, TASK, EVENT, RELATIONSHIP, SKILL, QUESTION, UNKNOWN.\n\n"
            f"History:\n{history}\n\n"
            f"User: {user_message}\n"
            f"Assistant: {assistant_response}\n\n"
            "JSON Format:\n"
            "{\n"
            '  "memories": [\n'
            '    {"title": "string", "content": "string", "memory_type": "string"}\n'
            "  ]\n"
            "}"
        )

        try:
            # We want structured output, but we can just ask Gemini to return JSON and parse it.
            # In a real implementation with Gemini 1.5 Pro, we could use the new `response_schema` feature,
            # but since `llm_service.py` currently just uses `generate_answer` which returns text, we will parse the JSON.
            result_text = self.llm_service.generate_answer(prompt, [])

            # Strip markdown JSON fences if any
            result_text = result_text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            data = json.loads(result_text)
            parsed = MemoryExtractionResult(**data)
            return parsed.memories
        except Exception as e:
            logger.error(f"Failed to extract memory via Gemini: {e}")
            return []
