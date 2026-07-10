from abc import ABC, abstractmethod
from typing import Callable
from app.services.llm.models import PipelineContext


class BaseMiddleware(ABC):
    """
    Abstract base class for all LLM Gateway middleware.
    Middleware can modify the context.request before it hits the provider,
    or modify the context.response after it returns.
    """

    @abstractmethod
    def process(
        self,
        context: PipelineContext,
        next_middleware: Callable[[PipelineContext], None],
    ) -> None:
        """
        Process the request/response.
        Must call `next_middleware(context)` to continue the chain.
        """
        pass
