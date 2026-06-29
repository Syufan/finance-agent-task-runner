from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.api.routes import create_router
from app.api.schemas import RunAgentRequest


@dataclass
class FakeRunResult:
    status: str
    finalAnswer: str
    actions: list[str]
    traceId: str


@dataclass
class FakeStep:
    stepId: str
    stepName: str
    toolName: str
    input: dict
    output: dict
    status: str
    error: str | None
    startedAt: datetime
    durationMs: int


@dataclass
class FakeTrace:
    traceId: str
    userRequest: str
    steps: list[dict]
    finalAnswer: str


class FakeAgentRunner:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def run(self, user_request: str) -> FakeRunResult:
        self.calls.append(user_request)
        return FakeRunResult(
            status="completed",
            finalAnswer=f"mocked answer for {user_request}",
            actions=["invoice_lookup", "policy_lookup"],
            traceId="trace-123",
        )


class FakeTraceStore:
    def __init__(self) -> None:
        self.requested_ids: list[str] = []
        self.trace = FakeTrace(
            traceId="trace-123",
            userRequest="Please check invoice INV-1001",
            steps=[
                {
                    "stepId": "step-001",
                    "stepName": "Lookup invoice",
                    "toolName": "invoice_lookup",
                    "input": {"invoiceId": "INV-1001"},
                    "output": {"invoiceId": "INV-1001"},
                    "status": "success",
                    "error": None,
                    "startedAt": datetime(2026, 6, 28, 10, 0, tzinfo=timezone.utc),
                    "durationMs": 5,
                }
            ],
            finalAnswer="mocked answer",
        )

    def get(self, trace_id: str) -> FakeTrace | None:
        self.requested_ids.append(trace_id)
        if trace_id == self.trace.traceId:
            return self.trace
        return None


def _route_by_path(router, path: str):
    return next(route for route in router.routes if getattr(route, "path", None) == path)


class AgentRoutesTestCase(unittest.TestCase):
    def test_create_router_registers_expected_paths(self) -> None:
        router = create_router(FakeAgentRunner(), FakeTraceStore())
        paths = {route.path for route in router.routes if hasattr(route, "path")}

        self.assertEqual(paths, {"/health", "/agent/run", "/agent/traces/{trace_id}"})

    def test_run_agent_request_uses_camel_case_alias(self) -> None:
        request = RunAgentRequest.model_validate({"userRequest": "Check INV-1001"})

        self.assertEqual(request.userRequest, "Check INV-1001")

    def test_run_agent_uses_injected_runner(self) -> None:
        agent_runner = FakeAgentRunner()
        trace_store = FakeTraceStore()
        router = create_router(agent_runner, trace_store)
        route = _route_by_path(router, "/agent/run")

        request = RunAgentRequest.model_validate({"userRequest": "Check INV-1001"})
        response = route.endpoint(request)

        self.assertEqual(agent_runner.calls, ["Check INV-1001"])
        self.assertEqual(response.status, "completed")
        self.assertEqual(response.finalAnswer, "mocked answer for Check INV-1001")
        self.assertEqual(response.actions, ["invoice_lookup", "policy_lookup"])
        self.assertEqual(response.traceId, "trace-123")

    def test_get_trace_uses_injected_trace_store(self) -> None:
        agent_runner = FakeAgentRunner()
        trace_store = FakeTraceStore()
        router = create_router(agent_runner, trace_store)
        route = _route_by_path(router, "/agent/traces/{trace_id}")

        response = route.endpoint("trace-123")

        self.assertEqual(trace_store.requested_ids, ["trace-123"])
        self.assertEqual(response.traceId, "trace-123")
        self.assertEqual(response.userInput, "Please check invoice INV-1001")
        self.assertEqual(response.finalAnswer, "mocked answer")
        self.assertEqual(len(response.steps), 1)
        self.assertEqual(response.steps[0].toolName, "invoice_lookup")
        self.assertEqual(response.steps[0].startedAt.tzinfo, timezone.utc)

    def test_get_trace_returns_404_for_missing_trace(self) -> None:
        agent_runner = FakeAgentRunner()
        trace_store = FakeTraceStore()
        router = create_router(agent_runner, trace_store)
        route = _route_by_path(router, "/agent/traces/{trace_id}")

        with self.assertRaises(HTTPException) as context:
            route.endpoint("trace-missing")

        self.assertEqual(context.exception.status_code, 404)
