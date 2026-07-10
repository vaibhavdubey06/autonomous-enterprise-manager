from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PromptAsset(BaseModel):
    """A first-class prompt asset."""

    id: str
    version: str = "1.0.0"
    description: str
    template: str
    variables: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CompiledPrompt(BaseModel):
    """Result of the Prompt Compiler."""

    text: str
    asset_id: Optional[str] = None
    variables_injected: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
