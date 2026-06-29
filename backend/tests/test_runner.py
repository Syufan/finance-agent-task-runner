from pathlib import Path
import sys
import unittest
from datetime import datetime


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.agent.context import AgentContext, LookupState
from app.agent.errors import AgentError
from app.agent.planner import ActionType, NextAction
from app.agent.runner import AgentRunner
from app.agent.trace import AgentTrace
from app.domain.models import Invoice, Policy, PurchaseOrder


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


class SequencePlanner:
    def __init__(self, actions: list[NextAction]) -> None:
        self._actions = actions
        self.calls: list[AgentContext] = []

    def decide(self, context: AgentContext) -> NextAction:
        self.calls.append(context)
        if not self._actions:
            raise AssertionError("Planner was called more times than expected")
        return self._actions.pop(0)


class StaticTool:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error
        self.calls: list[dict] = []

    def execute(self, tool_input: dict) -> object:
        self.calls.append(tool_input)
        if self._error is not None:
            raise self._error
        return self._result


class FakeToolRegistry:
    def __init__(self) -> None:
        self.calls: list[str | None] = []
        self.tools: dict[str, object] = {}

    def get(self, tool_name: str | None):
        self.calls.append(tool_name)
        if tool_name is None:
            raise AssertionError("Tool name should not be None")
        if tool_name not in self.tools:
            raise AssertionError(f"Unexpected tool call: {tool_name}")
        return self.tools[tool_name]


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
        self.assertEqual(trace_store.saved_traces[0].userRequest, "Please help check this invoice")

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
        self.assertEqual(len(trace_store.saved_traces[0].steps), 1)
        self.assertEqual(trace_store.saved_traces[0].steps[0]["stepName"], "input_validation")
        self.assertEqual(trace_store.saved_traces[0].steps[0]["status"], "failed")

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

    def test_finish_with_message_returns_completed(self) -> None:
        planner = FakePlanner(
            NextAction(
                type=ActionType.FINISH,
                message="Invoice review completed.",
            )
        )
        tool_registry = FakeToolRegistry()
        trace_store = FakeTraceStore()
        runner = AgentRunner(planner, tool_registry, trace_store)

        result = runner.run("Please check invoice INV-1001")

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.finalAnswer, "Invoice review completed.")

    def test_execute_tool_action_updates_context_when_invoice_lookup_returns_invoice(self) -> None:
        planner = FakePlanner(NextAction(type=ActionType.FINISH, message="unused"))
        tool_registry = FakeToolRegistry()
        tool_registry.tools["invoice_lookup"] = StaticTool(
            result=Invoice(
                invoiceId="INV-1001",
                vendor="Acme",
                amount=1000,
                currency="USD",
                status="blocked",
                poId="PO-9001",
                blockReason="PO_AMOUNT_MISMATCH",
            )
        )
        runner = AgentRunner(planner, tool_registry, FakeTraceStore())
        context = AgentContext(invoice_id="INV-1001")
        trace = AgentTrace(userRequest="Please check invoice INV-1001")
        actions: list[str] = []

        runner._execute_tool_action(
            context=context,
            trace=trace,
            actions=actions,
            tool_name="invoice_lookup",
            tool_input={"invoiceId": "INV-1001"},
        )

        self.assertEqual(actions, ["invoice_lookup"])
        self.assertEqual(context.invoice_lookup_state, LookupState.FOUND)
        self.assertIsNotNone(context.invoice)
        self.assertEqual(context.invoice.invoiceId, "INV-1001")
        self.assertEqual(len(trace.steps), 1)
        self.assertEqual(trace.steps[0]["status"], "success")

    def test_execute_tool_action_sets_not_found_when_tool_returns_none(self) -> None:
        planner = FakePlanner(NextAction(type=ActionType.FINISH, message="unused"))
        tool_registry = FakeToolRegistry()
        tool_registry.tools["invoice_lookup"] = StaticTool(result=None)
        runner = AgentRunner(planner, tool_registry, FakeTraceStore())
        context = AgentContext(invoice_id="INV-9999")
        trace = AgentTrace(userRequest="Please check invoice INV-9999")

        runner._execute_tool_action(
            context=context,
            trace=trace,
            actions=[],
            tool_name="invoice_lookup",
            tool_input={"invoiceId": "INV-9999"},
        )

        self.assertEqual(context.invoice_lookup_state, LookupState.NOT_FOUND)
        self.assertEqual(len(trace.steps), 1)
        self.assertEqual(trace.steps[0]["status"], "success")
        self.assertEqual(trace.steps[0]["output"], {})

    def test_execute_tool_action_sets_failed_state_and_trace_on_tool_error(self) -> None:
        planner = FakePlanner(NextAction(type=ActionType.FINISH, message="unused"))
        tool_registry = FakeToolRegistry()
        tool_registry.tools["policy_lookup"] = StaticTool(
            error=RuntimeError("policy service unavailable")
        )
        runner = AgentRunner(planner, tool_registry, FakeTraceStore())
        context = AgentContext(invoice_id="INV-1001")
        trace = AgentTrace(userRequest="Please check invoice INV-1001")

        runner._execute_tool_action(
            context=context,
            trace=trace,
            actions=[],
            tool_name="policy_lookup",
            tool_input={"blockReason": "PO_AMOUNT_MISMATCH"},
        )

        self.assertEqual(context.policy_lookup_state, LookupState.FAILED)
        self.assertIsNotNone(context.error)
        self.assertEqual(context.error.code, "TOOL_EXECUTION_FAILED")
        self.assertEqual(context.error.source, "policy_lookup")
        self.assertEqual(len(trace.steps), 1)
        self.assertEqual(trace.steps[0]["status"], "failed")

    def test_invoice_lookup_success_should_allow_next_planner_decision(self) -> None:
        planner = SequencePlanner(
            [
                NextAction(
                    type=ActionType.CALL_TOOL,
                    tool_name="invoice_lookup",
                    tool_input={"invoiceId": "INV-1001"},
                ),
                NextAction(
                    type=ActionType.FINISH,
                    message="Moved to next planner step.",
                ),
            ]
        )
        tool_registry = FakeToolRegistry()
        tool_registry.tools["invoice_lookup"] = StaticTool(
            result=Invoice(
                invoiceId="INV-1001",
                vendor="Acme",
                amount=1000,
                currency="USD",
                status="paid",
                poId=None,
                blockReason=None,
            )
        )
        trace_store = FakeTraceStore()
        runner = AgentRunner(planner, tool_registry, trace_store)

        result = runner.run("Please check invoice INV-1001")

        self.assertEqual(result.status, "completed")
        self.assertEqual(tool_registry.calls, ["invoice_lookup"])
        self.assertEqual(len(planner.calls), 2)
        self.assertEqual(planner.calls[1].invoice_lookup_state, LookupState.FOUND)

    def test_happy_path_runs_tools_in_order_and_completes(self) -> None:
        planner = SequencePlanner(
            [
                NextAction(
                    type=ActionType.CALL_TOOL,
                    tool_name="invoice_lookup",
                    tool_input={"invoiceId": "INV-1001"},
                ),
                NextAction(
                    type=ActionType.CALL_TOOL,
                    tool_name="po_lookup",
                    tool_input={"poId": "PO-9001"},
                ),
                NextAction(
                    type=ActionType.CALL_TOOL,
                    tool_name="policy_lookup",
                    tool_input={"blockReason": "PO_AMOUNT_MISMATCH"},
                ),
                NextAction(
                    type=ActionType.FINISH,
                    message="Investigation completed.",
                ),
            ]
        )
        tool_registry = FakeToolRegistry()
        tool_registry.tools["invoice_lookup"] = StaticTool(
            result=Invoice(
                invoiceId="INV-1001",
                vendor="Acme",
                amount=1000,
                currency="USD",
                status="blocked",
                poId="PO-9001",
                blockReason="PO_AMOUNT_MISMATCH",
            )
        )
        tool_registry.tools["po_lookup"] = StaticTool(
            result=PurchaseOrder(
                poId="PO-9001",
                amount=1000,
                currency="USD",
                owner="Jane",
                status="approved",
            )
        )
        tool_registry.tools["policy_lookup"] = StaticTool(
            result=Policy(
                blockReason="PO_AMOUNT_MISMATCH",
                policy="Match PO amount",
                recommendedAction="Review variance",
            )
        )
        trace_store = FakeTraceStore()
        runner = AgentRunner(planner, tool_registry, trace_store)

        result = runner.run("Please check invoice INV-1001")

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.actions, ["invoice_lookup", "po_lookup", "policy_lookup"])
        self.assertEqual([step["toolName"] for step in trace_store.saved_traces[0].steps], ["invoice_lookup", "po_lookup", "policy_lookup"])


if __name__ == "__main__":
    unittest.main()
