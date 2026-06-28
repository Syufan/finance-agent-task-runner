from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentTrace:
    userRequest: str
    steps: list[dict] = field(default_factory=list)
    finalAnswer: str | None = None


class TraceStore:
    def get(self, trace_id: str):
        pass
