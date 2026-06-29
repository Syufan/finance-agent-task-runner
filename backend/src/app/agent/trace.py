from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class TraceStep:
    # One agent decision or tool call.
    stepId: str
    stepName: str
    toolName: str | None
    input: dict[str, Any]
    output: dict[str, Any]
    status: str
    error: str | None
    startedAt: datetime
    durationMs: int


@dataclass
class AgentTrace:
    # Trace for one agent run.
    userRequest: str

    # Unique trace ID.
    traceId: str = field(default_factory=lambda: str(uuid4()))

    # Planner decisions and tool calls.
    steps: list[TraceStep] = field(default_factory=list)

    # Final answer returned to the user.
    finalAnswer: str | None = None


class TraceStore:
    def __init__(self) -> None:
        # Store traces in memory.
        self._traces: dict[str, AgentTrace] = {}

    def save(self, trace: AgentTrace) -> None:
        # Save one trace.
        self._traces[trace.traceId] = trace

    def get(self, trace_id: str) -> AgentTrace | None:
        # Find one trace by ID.
        return self._traces.get(trace_id)