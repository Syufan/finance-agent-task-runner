from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.domain.models import Invoice
from app.repositories.invoice_repository import InvoiceRepository


class FakeJsonDataSource:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows
        self.calls: list[str] = []

    def load(self, filename: str) -> list[dict]:
        self.calls.append(filename)
        return self._rows


class InvoiceRepositoryTestCase(unittest.TestCase):
    def test_find_by_id_loads_invoices_file(self) -> None:
        data_source = FakeJsonDataSource(rows=[])
        repository = InvoiceRepository(data_source)

        repository.find_by_id("INV-1001")

        self.assertEqual(data_source.calls, ["invoices.json"])

    def test_find_by_id_returns_invoice_model_when_found(self) -> None:
        data_source = FakeJsonDataSource(
            rows=[
                {
                    "invoiceId": "INV-1001",
                    "vendor": "Acme",
                    "amount": 1000,
                    "currency": "USD",
                    "status": "blocked",
                    "poId": "PO-9001",
                    "blockReason": "PO_AMOUNT_MISMATCH",
                }
            ]
        )
        repository = InvoiceRepository(data_source)

        result = repository.find_by_id("INV-1001")

        self.assertEqual(
            result,
            Invoice(
                invoiceId="INV-1001",
                vendor="Acme",
                amount=1000,
                currency="USD",
                status="blocked",
                poId="PO-9001",
                blockReason="PO_AMOUNT_MISMATCH",
            ),
        )

    def test_find_by_id_returns_none_when_invoice_is_missing(self) -> None:
        data_source = FakeJsonDataSource(
            rows=[
                {
                    "invoiceId": "INV-1001",
                    "vendor": "Acme",
                    "amount": 1000,
                    "currency": "USD",
                    "status": "blocked",
                    "poId": "PO-9001",
                    "blockReason": "PO_AMOUNT_MISMATCH",
                }
            ]
        )
        repository = InvoiceRepository(data_source)

        result = repository.find_by_id("INV-9999")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
