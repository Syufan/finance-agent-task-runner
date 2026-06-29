from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.agent.context import AgentContext, LookupState
from app.domain.models import Invoice, Policy, PurchaseOrder


class AgentContextTestCase(unittest.TestCase):
    def test_context_defaults_to_empty_lookup_state(self) -> None:
        context = AgentContext()

        self.assertIsNone(context.invoice_id)
        self.assertIsNone(context.invoice)
        self.assertEqual(context.invoice_lookup_state, LookupState.NOT_STARTED)
        self.assertFalse(context.invoice_lookup_attempted)

        self.assertIsNone(context.purchase_order)
        self.assertEqual(context.po_lookup_state, LookupState.NOT_STARTED)
        self.assertFalse(context.po_lookup_attempted)

        self.assertIsNone(context.policy)
        self.assertEqual(context.policy_lookup_state, LookupState.NOT_STARTED)
        self.assertFalse(context.policy_lookup_attempted)

        self.assertIsNone(context.error)

    def test_context_can_be_initialized_with_invoice_id(self) -> None:
        context = AgentContext(invoice_id="INV-1001")

        self.assertEqual(context.invoice_id, "INV-1001")

    def test_context_can_hold_tool_results(self) -> None:
        invoice = Invoice(
            invoiceId="INV-1001",
            vendor="ABC Logistics",
            amount=12000,
            currency="EUR",
            status="blocked",
            poId="PO-9001",
            blockReason="PO_AMOUNT_MISMATCH",
        )
        purchase_order = PurchaseOrder(
            poId="PO-9001",
            amount=10000,
            currency="EUR",
            owner="john.smith@example.com",
            status="active",
        )
        policy = Policy(
            blockReason="PO_AMOUNT_MISMATCH",
            policy="If invoice amount is higher than PO amount, requester must confirm whether the PO should be amended before payment can proceed.",
            recommendedAction="Contact PO owner for confirmation.",
        )

        context = AgentContext(
            invoice_id="INV-1001",
            invoice=invoice,
            purchase_order=purchase_order,
            policy=policy,
        )

        self.assertEqual(context.invoice.invoiceId, "INV-1001")
        self.assertEqual(context.purchase_order.poId, "PO-9001")
        self.assertEqual(context.policy.blockReason, "PO_AMOUNT_MISMATCH")
