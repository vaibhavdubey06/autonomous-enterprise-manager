from typing import Any, Dict, List
from pydantic import BaseModel, Field


class EnterpriseContext(BaseModel):
    """Structured data model containing gathered context for LLM compilation."""

    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    semantic_memory: List[str] = Field(default_factory=list)
    retrieved_documents: List[str] = Field(default_factory=list)
    workflow_state: Dict[str, Any] = Field(default_factory=dict)
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    governance_policies: List[str] = Field(default_factory=list)
    agent_profile: Dict[str, Any] = Field(default_factory=dict)

    def to_formatted_string(self) -> str:
        """Converts the structured context into a single string block if needed by simple templates."""
        parts = []
        if self.conversation_history:
            parts.append("Conversation History:")
            for msg in self.conversation_history:
                parts.append(f"{msg.get('role', 'user')}: {msg.get('content', '')}")

        if self.semantic_memory:
            parts.append("Semantic Memory:\n" + "\n".join(self.semantic_memory))

        if self.retrieved_documents:
            parts.append("Retrieved Knowledge:\n" + "\n".join(self.retrieved_documents))

        if self.workflow_state:
            parts.append(f"Workflow State:\n{self.workflow_state}")

        if self.execution_context:
            parts.append(f"Execution Context:\n{self.execution_context}")

        if self.governance_policies:
            parts.append("Governance Policies:\n" + "\n".join(self.governance_policies))

        if self.agent_profile:
            parts.append(f"Agent Profile:\n{self.agent_profile}")

        return "\n\n".join(parts)
