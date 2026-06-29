from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.agent.context import AgentContext
from app.agent.errors import AgentError
from app.agent.planner import ActionType, NextAction
from app.agent.runner import AgentRunner


class FakePlanner:
    def __init__(self, action: NextAction) -> None:
        self._action = action
        self.calls: list[AgentContext] = []

    def decide(self, context: AgentContext) -> NextAction:
        self.calls.append(context)
        return self._action


class FailIfCalledPlanner:
    def __init__(self) -> None:
        self.calls = 0

    def decide(self, context: AgentContext) -> NextAction:
        self.calls += 1
        raise AssertionError("Planner should not be called")


class FakeToolRegistry:
    def __init__(self) -> None:
        self.calls: list[str | None] = []

    def get(self, tool_name: str | None):
        self.calls.append(tool_name)
        raise AssertionError("Tool should not be called")


class FakeTraceStore:
    def __init__(self) -> None:
        self.saved_traces: list[object] = []

    def save(self, trace: object) -> None:
        self.saved_traces.append(trace)


class RunnerTestCase(unittest.TestCase):
    def test_missing_invoice_id_returns_needs_input_without_calling_tool(self) -> None:
        planner = FakePlanner(
            NextAction(
                type=ActionType.ASK_CLARIFICATION,
                message="Please provide an invoice ID.",
            )
        )
        tool_registry = FakeToolRegistry()
        trace_store = FakeTraceStore()
        runner = AgentRunner(planner, tool_registry, trace_store)

        result = runner.run("Please help check this invoice")

        self.assertEqual(result.status, "needs_input")
        self.assertEqual(result.finalAnswer, "Please provide an invoice ID.")
        self.assertEqual(len(planner.calls), 1)
        self.assertIsNone(planner.calls[0].invoice_id)
        self.assertEqual(tool_registry.calls, [])
        self.assertEqual(len(trace_store.saved_traces), 1)

    def test_invalid_invoice_id_returns_failed_without_calling_planner(self) -> None:
        planner = FailIfCalledPlanner()
        tool_registry = FakeToolRegistry()
        trace_store = FakeTraceStore()
        runner = AgentRunner(planner, tool_registry, trace_store)

        result = runner.run("Please check invoice INV-12A")

        self.assertEqual(result.status, "failed")
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.code, "INVALID_INVOICE_ID")
        self.assertEqual(planner.calls, 0)
        self.assertEqual(tool_registry.calls, [])
        self.assertEqual(len(trace_store.saved_traces), 1)

    def test_valid_invoice_id_builds_context_before_calling_planner(self) -> None:
        planner = FakePlanner(
            NextAction(
                type=ActionType.FINISH,
                error=AgentError(
                    code="INVOICE_NOT_FOUND",
                    message="Invoice INV-1001 was not found.",
                    source="invoice_lookup",
                ),
            )
        )
        tool_registry = FakeToolRegistry()
        trace_store = FakeTraceStore()
        runner = AgentRunner(planner, tool_registry, trace_store)

        runner.run("Please check invoice inv-1001")

        self.assertEqual(len(planner.calls), 1)
        self.assertEqual(planner.calls[0].invoice_id, "INV-1001")

    def test_planner_finish_with_error_returns_failed_and_saves_trace(self) -> None:
        planner = FakePlanner(
            NextAction(
                type=ActionType.FINISH,
                error=AgentError(
                    code="INVOICE_NOT_FOUND",
                    message="Invoice INV-1001 was not found.",
                    source="invoice_lookup",
                ),
            )
        )
        tool_registry = FakeToolRegistry()
        trace_store = FakeTraceStore()
        runner = AgentRunner(planner, tool_registry, trace_store)

        result = runner.run("Please check invoice INV-1001")

        self.assertEqual(result.status, "failed")
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.code, "INVOICE_NOT_FOUND")
        self.assertEqual(result.finalAnswer, "Invoice INV-1001 was not found.")
        self.assertEqual(len(trace_store.saved_traces), 1)


if __name__ == "__main__":
    unittest.main()
