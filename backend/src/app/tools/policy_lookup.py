from __future__ import annotations

from app.tools.base import Tool


class PolicyLookupTool(Tool):
    name = "policy_lookup"

    def __init__(self, repository) -> None:
        self._repository = repository
