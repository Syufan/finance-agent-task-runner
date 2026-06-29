from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.domain.models import PurchaseOrder
from app.tools.po_lookup import POLookupTool


class FakePORepository:
    def __init__(self, purchase_order: PurchaseOrder | None) -> None:
        self._purchase_order = purchase_order
        self.calls: list[str] = []

    def find_by_id(self, po_id: str) -> PurchaseOrder | None:
        self.calls.append(po_id)
        return self._purchase_order


class POLookupToolTestCase(unittest.TestCase):
    def test_tool_exposes_po_lookup_name(self) -> None:
        tool = POLookupTool(FakePORepository(purchase_order=None))

        self.assertEqual(tool.name, "po_lookup")

    def test_execute_calls_repository_with_po_id(self) -> None:
        purchase_order = PurchaseOrder(
            poId="PO-9001",
            amount=1000,
            currency="USD",
            owner="Jane",
            status="approved",
        )
        repository = FakePORepository(purchase_order=purchase_order)
        tool = POLookupTool(repository)

        tool.execute({"poId": "PO-9001"})

        self.assertEqual(repository.calls, ["PO-9001"])

    def test_execute_returns_none_when_po_is_missing(self) -> None:
        repository = FakePORepository(purchase_order=None)
        tool = POLookupTool(repository)

        result = tool.execute({"poId": "PO-9999"})

        self.assertIsNone(result)

    def test_execute_returns_purchase_order(self) -> None:
        purchase_order = PurchaseOrder(
            poId="PO-9001",
            amount=1000,
            currency="USD",
            owner="Jane",
            status="approved",
        )
        repository = FakePORepository(purchase_order=purchase_order)
        tool = POLookupTool(repository)

        result = tool.execute({"poId": "PO-9001"})

        self.assertEqual(result, purchase_order)


if __name__ == "__main__":
    unittest.main()
