from app.data.json_data_source import JsonDataSource
from app.domain.models import Policy


class PolicyRepository:
    def __init__(self, data_source: JsonDataSource) -> None:
        self._data_source = data_source

    def find_by_block_reason(self, block_reason: str) -> Policy | None:
        policies = self._data_source.load("policies.json")

        for item in policies:
            if item["blockReason"] == block_reason:
                return Policy(
                    blockReason=item["blockReason"],
                    policy=item["policy"],
                    recommendedAction=item["recommendedAction"],
                )

        return None