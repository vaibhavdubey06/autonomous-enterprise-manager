from typing import Dict, List
from abc import ABC, abstractmethod
from app.services.retrieval.models import QueryContext, RetrievedChunk


class BaseRetrievalStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def retrieve(self, context: QueryContext) -> List[RetrievedChunk]:
        """Execute the retrieval strategy."""
        pass


class RetrievalStrategyRegistry:
    def __init__(self):
        self._strategies: Dict[str, BaseRetrievalStrategy] = {}

    def register(self, strategy: BaseRetrievalStrategy):
        self._strategies[strategy.name] = strategy

    def get_strategy(self, name: str) -> BaseRetrievalStrategy:
        if name not in self._strategies:
            raise ValueError(f"Retrieval strategy {name} not found.")
        return self._strategies[name]

    def get_all(self) -> Dict[str, BaseRetrievalStrategy]:
        return self._strategies


# Global registry instance
strategy_registry = RetrievalStrategyRegistry()
