from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RunAgentRequest(BaseModel):
    userRequest: str


class RunAgentResponse(BaseModel):
    status: str
    finalAnswer: str
    actions: list[str]
    traceId: str


class StepResponse(BaseModel):
    stepId: str
    stepName: str
    toolName: str
    input: dict[str, Any]
    output: dict[str, Any]
    status: str
    error: str | None = None
    startedAt: datetime
    durationMs: int


class TraceResponse(BaseModel):
    traceId: str
    userInput: str
    steps: list[StepResponse]
    finalAnswer: str