from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.domain.models import Policy
from app.repositories.policy_repository import PolicyRepository


class FakeJsonDataSource:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows
        self.calls: list[str] = []

    def load(self, filename: str) -> list[dict]:
        self.calls.append(filename)
        return self._rows


class PolicyRepositoryTestCase(unittest.TestCase):
    def test_find_by_block_reason_loads_policies_file(self) -> None:
        data_source = FakeJsonDataSource(rows=[])
        repository = PolicyRepository(data_source)

        repository.find_by_block_reason("PO_AMOUNT_MISMATCH")

        self.assertEqual(data_source.calls, ["policies.json"])

    def test_find_by_block_reason_returns_policy_when_found(self) -> None:
        data_source = FakeJsonDataSource(
            rows=[
                {
                    "blockReason": "PO_AMOUNT_MISMATCH",
                    "policy": "Match PO amount",
                    "recommendedAction": "Review variance",
                }
            ]
        )
        repository = PolicyRepository(data_source)

        result = repository.find_by_block_reason("PO_AMOUNT_MISMATCH")

        self.assertEqual(
            result,
            Policy(
                blockReason="PO_AMOUNT_MISMATCH",
                policy="Match PO amount",
                recommendedAction="Review variance",
            ),
        )

    def test_find_by_block_reason_returns_none_when_policy_is_missing(self) -> None:
        data_source = FakeJsonDataSource(
            rows=[
                {
                    "blockReason": "PO_AMOUNT_MISMATCH",
                    "policy": "Match PO amount",
                    "recommendedAction": "Review variance",
                }
            ]
        )
        repository = PolicyRepository(data_source)

        result = repository.find_by_block_reason("APPROVAL_PENDING")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
