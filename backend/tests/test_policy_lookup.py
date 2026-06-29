from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.domain.models import Policy
from app.tools.policy_lookup import PolicyLookupTool


class FakePolicyRepository:
    def __init__(self, policy: Policy | None) -> None:
        self._policy = policy
        self.calls: list[str] = []

    def find_by_block_reason(self, block_reason: str) -> Policy | None:
        self.calls.append(block_reason)
        return self._policy


class PolicyLookupToolTestCase(unittest.TestCase):
    def test_tool_exposes_policy_lookup_name(self) -> None:
        tool = PolicyLookupTool(FakePolicyRepository(policy=None))

        self.assertEqual(tool.name, "policy_lookup")

    def test_execute_calls_repository_with_block_reason(self) -> None:
        policy = Policy(
            blockReason="PO_AMOUNT_MISMATCH",
            policy="Match PO amount",
            recommendedAction="Review variance",
        )
        repository = FakePolicyRepository(policy=policy)
        tool = PolicyLookupTool(repository)

        tool.execute({"blockReason": "PO_AMOUNT_MISMATCH"})

        self.assertEqual(repository.calls, ["PO_AMOUNT_MISMATCH"])

    def test_execute_returns_none_when_policy_is_missing(self) -> None:
        repository = FakePolicyRepository(policy=None)
        tool = PolicyLookupTool(repository)

        result = tool.execute({"blockReason": "PO_AMOUNT_MISMATCH"})

        self.assertIsNone(result)

    def test_execute_returns_policy(self) -> None:
        policy = Policy(
            blockReason="PO_AMOUNT_MISMATCH",
            policy="Match PO amount",
            recommendedAction="Review variance",
        )
        repository = FakePolicyRepository(policy=policy)
        tool = PolicyLookupTool(repository)

        result = tool.execute({"blockReason": "PO_AMOUNT_MISMATCH"})

        self.assertEqual(result, policy)


if __name__ == "__main__":
    unittest.main()
