import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
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
    def __init__(self, directory: Path | None = None) -> None:
        # Store traces in memory and on disk.
        self._directory = directory or (Path(__file__).resolve().parents[1] / "data" / "traces")
        self._directory.mkdir(parents=True, exist_ok=True)
        self._traces: dict[str, AgentTrace] = {}

    def save(self, trace: AgentTrace) -> None:
        # Save one trace.
        self._traces[trace.traceId] = trace
        trace_path = self._trace_path(trace.traceId)
        trace_path.write_text(
            json.dumps(self._serialize_trace(trace), ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def get(self, trace_id: str) -> AgentTrace | None:
        # Find one trace by ID.
        cached_trace = self._traces.get(trace_id)
        if cached_trace is not None:
            return cached_trace

        trace_path = self._trace_path(trace_id)
        if not trace_path.exists():
            return None

        trace = self._deserialize_trace(
            json.loads(trace_path.read_text(encoding="utf-8"))
        )
        self._traces[trace_id] = trace
        return trace

    def _trace_path(self, trace_id: str) -> Path:
        return self._directory / f"{trace_id}.json"

    def _serialize_trace(self, trace: AgentTrace) -> dict[str, Any]:
        return {
            "traceId": trace.traceId,
            "userRequest": trace.userRequest,
            "steps": [
                {
                    **step,
                    "startedAt": step["startedAt"].isoformat()
                    if isinstance(step.get("startedAt"), datetime)
                    else step.get("startedAt"),
                }
                for step in trace.steps
            ],
            "finalAnswer": trace.finalAnswer,
        }

    def _deserialize_trace(self, payload: dict[str, Any]) -> AgentTrace:
        trace = AgentTrace(
            userRequest=payload["userRequest"],
            traceId=payload["traceId"],
            finalAnswer=payload.get("finalAnswer"),
        )
        trace.steps = [
            {
                **step,
                "startedAt": datetime.fromisoformat(step["startedAt"])
                if step.get("startedAt")
                else None,
            }
            for step in payload.get("steps", [])
        ]
        return trace
