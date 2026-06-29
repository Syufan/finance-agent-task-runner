from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.domain.models import PurchaseOrder
from app.repositories.po_repository import PORepository


class FakeJsonDataSource:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows
        self.calls: list[str] = []

    def load(self, filename: str) -> list[dict]:
        self.calls.append(filename)
        return self._rows


class PORepositoryTestCase(unittest.TestCase):
    def test_find_by_id_loads_purchase_orders_file(self) -> None:
        data_source = FakeJsonDataSource(rows=[])
        repository = PORepository(data_source)

        repository.find_by_id("PO-9001")

        self.assertEqual(data_source.calls, ["purchase_orders.json"])

    def test_find_by_id_returns_purchase_order_when_found(self) -> None:
        data_source = FakeJsonDataSource(
            rows=[
                {
                    "poId": "PO-9001",
                    "amount": 1000,
                    "currency": "USD",
                    "owner": "Jane",
                    "status": "approved",
                }
            ]
        )
        repository = PORepository(data_source)

        result = repository.find_by_id("PO-9001")

        self.assertEqual(
            result,
            PurchaseOrder(
                poId="PO-9001",
                amount=1000,
                currency="USD",
                owner="Jane",
                status="approved",
            ),
        )

    def test_find_by_id_returns_none_when_purchase_order_is_missing(self) -> None:
        data_source = FakeJsonDataSource(
            rows=[
                {
                    "poId": "PO-9001",
                    "amount": 1000,
                    "currency": "USD",
                    "owner": "Jane",
                    "status": "approved",
                }
            ]
        )
        repository = PORepository(data_source)

        result = repository.find_by_id("PO-9999")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
