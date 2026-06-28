from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "src" / "app" / "data"


class DataFileTestCase(unittest.TestCase):
    def test_invoice_fixture_is_valid_json(self) -> None:
        with (DATA_DIR / "invoices.json").open("r", encoding="utf-8") as f:
            invoices = json.load(f)

        self.assertIsInstance(invoices, list)
        self.assertGreater(len(invoices), 0)
        self.assertIn("invoiceId", invoices[0])
        self.assertIn("status", invoices[0])

    def test_purchase_orders_fixture_is_valid_json(self) -> None:
        with (DATA_DIR / "pruchase_orders.json").open("r", encoding="utf-8") as f:
            purchase_orders = json.load(f)

        self.assertIsInstance(purchase_orders, list)
        self.assertGreater(len(purchase_orders), 0)
        self.assertIn("poId", purchase_orders[0])
        self.assertIn("owner", purchase_orders[0])

    def test_policies_fixture_is_valid_json(self) -> None:
        with (DATA_DIR / "policies.json").open("r", encoding="utf-8") as f:
            policies = json.load(f)

        self.assertIsInstance(policies, list)
        self.assertGreater(len(policies), 0)
        self.assertIn("blockReason", policies[0])
        self.assertIn("recommendedAction", policies[0])
