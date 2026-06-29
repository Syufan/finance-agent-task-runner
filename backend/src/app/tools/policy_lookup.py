from typing import Any

from app.domain.models import Policy
from app.repositories.policy_repository import PolicyRepository
from app.tools.base import Tool


class PolicyLookupTool(Tool):
    name = "policy_lookup"
    description = "Look up the policy and recommended action for a block reason."
    input_schema = {
        "blockReason": "string",
    }

    def __init__(self, policy_repository: PolicyRepository) -> None:
        self._policy_repository = policy_repository

    def execute(
        self,
        tool_input: dict[str, Any],
    ) -> Policy | None:
        block_reason = str(tool_input["blockReason"])
        return self._policy_repository.find_by_block_reason(block_reason)