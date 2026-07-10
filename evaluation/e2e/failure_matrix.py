import contextlib
from unittest.mock import patch
from app.services.llm.exceptions import LLMProviderError, LLMTimeoutError


class FailureInjector:
    """
    Simulates external backend failures according to the scenario matrix.
    Injects timeouts, database outages, and connector failures dynamically.
    """

    @staticmethod
    @contextlib.contextmanager
    def inject(scenario: dict):
        patches = []
        try:
            # 1. Provider Failures
            if scenario.get("expected_provider") == "gemini_fallback":

                def mock_gemini_generate(*args, **kwargs):
                    raise LLMProviderError("Gemini API quota exceeded.")

                patches.append(
                    patch(
                        "app.services.llm.providers.gemini.GeminiProvider.generate",
                        side_effect=mock_gemini_generate,
                    )
                )
                patches.append(
                    patch(
                        "app.services.llm.providers.gemini.GeminiProvider.generate_structured",
                        side_effect=mock_gemini_generate,
                    )
                )

            elif scenario.get("failure_injection") == "timeout":

                def mock_timeout(*args, **kwargs):
                    raise LLMTimeoutError("LLM Provider timed out.")

                patches.append(
                    patch(
                        "app.services.llm.providers.gemini.GeminiProvider.generate",
                        side_effect=mock_timeout,
                    )
                )

            # 2. Database / Retrieval Failures
            if scenario.get("failure_injection") == "qdrant_down":

                def mock_qdrant(*args, **kwargs):
                    raise ConnectionError("Qdrant unavailable")

                patches.append(
                    patch(
                        "app.services.vectorstore.qdrant_service.get_client",
                        side_effect=mock_qdrant,
                    )
                )

            # 3. Connector Failures
            if scenario.get("failure_injection") == "github_down":

                def mock_github(*args, **kwargs):
                    raise ConnectionError("GitHub API is unreachable")

                patches.append(
                    patch(
                        "app.capabilities.tools.github.tool.GitHubCapability.execute",
                        side_effect=mock_github,
                    )
                )

            # Start all patches
            for p in patches:
                p.start()

            yield

        finally:
            # Stop all patches to ensure test isolation
            for p in patches:
                p.stop()
