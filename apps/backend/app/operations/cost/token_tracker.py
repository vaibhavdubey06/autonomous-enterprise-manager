import datetime
from typing import List, Dict
from collections import defaultdict


class TokenRecord:
    def __init__(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float = 0.0,
        prompt_type: str = "unknown",
        agent: str = "",
        workflow_id: str = "",
        conversation_id: str = "",
    ):
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens
        self.latency_ms = latency_ms
        self.prompt_type = prompt_type
        self.agent = agent
        self.workflow_id = workflow_id
        self.conversation_id = conversation_id
        self.timestamp = datetime.datetime.utcnow()


class TokenTracker:
    """Records per-call LLM token usage."""

    def __init__(self):
        self.records: List[TokenRecord] = []

    def record(
        self, model: str, input_tokens: int, output_tokens: int, **kwargs
    ) -> TokenRecord:
        rec = TokenRecord(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            **kwargs,
        )
        self.records.append(rec)
        return rec

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from character count (chars / 4)."""
        return max(1, len(text) // 4)

    def get_total_tokens(self) -> int:
        return sum(r.total_tokens for r in self.records)

    def get_by_agent(self) -> Dict[str, int]:
        by_agent: Dict[str, int] = defaultdict(int)
        for r in self.records:
            if r.agent:
                by_agent[r.agent] += r.total_tokens
        return dict(by_agent)
