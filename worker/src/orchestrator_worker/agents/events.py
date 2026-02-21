"""Agent-agnostic event types for structured output."""

import json
import time
from dataclasses import dataclass, field


@dataclass
class AgentEvent:
    """Normalized event emitted by any agent runner.

    Fields match what the UI's StructuredLogViewer expects.
    """

    type: str  # message, tool_call, tool_result, notification, complete
    id: str | None = None
    role: str | None = None
    content_type: str | None = None
    text: str | None = None
    name: str | None = None
    arguments: dict | None = None
    status: str | None = None
    output: str | None = None
    extension_id: str | None = None
    message: str | None = None
    total_tokens: int | None = None
    created: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Serialize, dropping None values."""
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"))
