from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.domain.models import Invoice
from app.tools.invoice_lookup import InvoiceLookupTool


class FakeInvoiceRepository:
    def __init__(self, invoice: Invoice | None) -> None:
        self._invoice = invoice
        self.calls: list[str] = []

    def find_by_id(self, invoice_id: str) -> Invoice | None:
        self.calls.append(invoice_id)
        return self._invoice


class InvoiceLookupToolTestCase(unittest.TestCase):
    def test_tool_exposes_invoice_lookup_name(self) -> None:
        tool = InvoiceLookupTool(FakeInvoiceRepository(invoice=None))

        self.assertEqual(tool.name, "invoice_lookup")

    def test_execute_calls_repository_with_invoice_id(self) -> None:
        invoice = Invoice(
            invoiceId="INV-1001",
            vendor="Acme",
            amount=1000,
            currency="USD",
            status="blocked",
            poId="PO-9001",
            blockReason="PO_AMOUNT_MISMATCH",
        )
        repository = FakeInvoiceRepository(invoice=invoice)
        tool = InvoiceLookupTool(repository)

        tool.execute({"invoiceId": "INV-1001"})

        self.assertEqual(repository.calls, ["INV-1001"])

    def test_execute_returns_none_when_invoice_is_missing(self) -> None:
        repository = FakeInvoiceRepository(invoice=None)
        tool = InvoiceLookupTool(repository)

        result = tool.execute({"invoiceId": "INV-9999"})

        self.assertIsNone(result)

    def test_execute_returns_serialized_invoice_data(self) -> None:
        invoice = Invoice(
            invoiceId="INV-1001",
            vendor="Acme",
            amount=1000,
            currency="USD",
            status="blocked",
            poId="PO-9001",
            blockReason="PO_AMOUNT_MISMATCH",
        )
        repository = FakeInvoiceRepository(invoice=invoice)
        tool = InvoiceLookupTool(repository)

        result = tool.execute({"invoiceId": "INV-1001"})

        self.assertEqual(result, invoice)


if __name__ == "__main__":
    unittest.main()
