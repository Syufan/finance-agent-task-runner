from types import SimpleNamespace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.agent.context import AgentContext, LookupState
from app.agent.planner import ActionType, Planner


def _invoice(
    *,
    status: str = "blocked",
    poId: str | None = None,
    blockReason: str | None = None,
):
    return SimpleNamespace(
        status=status,
        poId=poId,
        blockReason=blockReason,
    )


class PlannerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.planner = Planner()

    def test_missing_invoice_id_asks_for_clarification(self) -> None:
        context = AgentContext()

        action = self.planner.decide(context)

        self.assertEqual(action.type, ActionType.ASK_CLARIFICATION)
        self.assertIsNone(action.tool_name)
        self.assertIsNone(action.tool_input)
        self.assertIn("invoice ID", action.message or "")

    def test_invoice_lookup_has_not_started_calls_invoice_lookup(self) -> None:
        context = AgentContext(invoice_id="INV-1001")

        action = self.planner.decide(context)

        self.assertEqual(action.type, ActionType.CALL_TOOL)
        self.assertEqual(action.tool_name, "invoice_lookup")
        self.assertEqual(action.tool_input, {"invoiceId": "INV-1001"})

    def test_invoice_not_found_finishes_with_message(self) -> None:
        context = AgentContext(
            invoice_id="INV-9999",
            invoice_lookup_state=LookupState.NOT_FOUND,
        )

        action = self.planner.decide(context)

        self.assertEqual(action.type, ActionType.FINISH)
        self.assertIsNotNone(action.error)
        self.assertEqual(action.error.code, "INVOICE_NOT_FOUND")

    def test_invoice_already_paid_finishes_without_followup_tools(self) -> None:
        context = AgentContext(
            invoice_id="INV-1003",
            invoice_lookup_state=LookupState.FOUND,
            invoice=_invoice(status="paid"),
        )

        action = self.planner.decide(context)

        self.assertEqual(action.type, ActionType.FINISH)
        self.assertIsNone(action.tool_name)
        self.assertIsNone(action.tool_input)
        self.assertIsNone(action.message)
        self.assertIsNone(action.error)

    def test_blocked_invoice_requires_po_lookup(self) -> None:
        context = AgentContext(
            invoice_id="INV-1001",
            invoice_lookup_state=LookupState.FOUND,
            invoice=_invoice(status="blocked", poId="PO-9001"),
            po_lookup_state=LookupState.NOT_STARTED,
        )

        action = self.planner.decide(context)

        self.assertEqual(action.type, ActionType.CALL_TOOL)
        self.assertEqual(action.tool_name, "po_lookup")
        self.assertEqual(action.tool_input, {"poId": "PO-9001"})

    def test_blocked_invoice_requires_policy_lookup(self) -> None:
        context = AgentContext(
            invoice_id="INV-1001",
            invoice_lookup_state=LookupState.FOUND,
            invoice=_invoice(
                status="blocked",
                poId="PO-9001",
                blockReason="PO_AMOUNT_MISMATCH",
            ),
            po_lookup_state=LookupState.FOUND,
            policy_lookup_state=LookupState.NOT_STARTED,
        )

        action = self.planner.decide(context)

        self.assertEqual(action.type, ActionType.CALL_TOOL)
        self.assertEqual(action.tool_name, "policy_lookup")
        self.assertEqual(action.tool_input, {"blockReason": "PO_AMOUNT_MISMATCH"})

    def test_policy_not_found_finishes_with_message(self) -> None:
        context = AgentContext(
            invoice_id="INV-1001",
            invoice_lookup_state=LookupState.FOUND,
            invoice=_invoice(
                status="blocked",
                poId="PO-9001",
                blockReason="PO_AMOUNT_MISMATCH",
            ),
            po_lookup_state=LookupState.FOUND,
            policy_lookup_state=LookupState.NOT_FOUND,
        )

        action = self.planner.decide(context)

        self.assertEqual(action.type, ActionType.FINISH)
        self.assertIsNone(action.error)
        self.assertIn("partial answer", action.message or "")

    def test_policy_tool_failure_finishes_with_message(self) -> None:
        context = AgentContext(
            invoice_id="INV-1001",
            invoice_lookup_state=LookupState.FOUND,
            invoice=_invoice(
                status="blocked",
                poId="PO-9001",
                blockReason="PO_AMOUNT_MISMATCH",
            ),
            po_lookup_state=LookupState.FOUND,
            policy_lookup_state=LookupState.FAILED,
            error=SimpleNamespace(
                code="TOOL_EXECUTION_FAILED",
                message="policy lookup failed",
                source="policy_lookup",
            ),
        )

        action = self.planner.decide(context)

        self.assertEqual(action.type, ActionType.FINISH)
        self.assertIsNone(action.error)
        self.assertIn("partial answer", action.message or "")

    def test_blocked_invoice_with_all_required_data_finishes(self) -> None:
        context = AgentContext(
            invoice_id="INV-1001",
            invoice_lookup_state=LookupState.FOUND,
            invoice=_invoice(
                status="blocked",
                poId="PO-9001",
                blockReason="PO_AMOUNT_MISMATCH",
            ),
            po_lookup_state=LookupState.FOUND,
            policy_lookup_state=LookupState.FOUND,
        )

        action = self.planner.decide(context)

        self.assertEqual(action.type, ActionType.FINISH)
        self.assertIsNone(action.message)
        self.assertIsNone(action.error)

    def test_pending_approval_invoice_finishes(self) -> None:
        context = AgentContext(
            invoice_id="INV-1002",
            invoice_lookup_state=LookupState.FOUND,
            invoice=_invoice(
                status="pending_approval",
                blockReason="APPROVAL_PENDING",
            ),
            policy_lookup_state=LookupState.FOUND,
        )

        action = self.planner.decide(context)

        self.assertEqual(action.type, ActionType.FINISH)
        self.assertIsNone(action.message)
        self.assertIsNone(action.error)

    def test_other_tool_failure_finishes_with_message(self) -> None:
        context = AgentContext(
            invoice_id="INV-1001",
            invoice_lookup_state=LookupState.FAILED,
            error=SimpleNamespace(
                code="TOOL_EXECUTION_FAILED",
                message="invoice lookup failed",
                source="invoice_lookup",
            ),
        )

        action = self.planner.decide(context)

        self.assertEqual(action.type, ActionType.FINISH)
        self.assertIsNotNone(action.error)
        self.assertEqual(action.error.source, "invoice_lookup")
