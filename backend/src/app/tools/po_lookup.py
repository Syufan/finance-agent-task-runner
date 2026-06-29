from typing import Any

from app.domain.models import PurchaseOrder
from app.repositories.po_repository import PORepository
from app.tools.base import Tool


class POLookupTool(Tool):
    name = "po_lookup"
    description = "Look up a purchase order by PO ID."
    input_schema = {
        "poId": "string",
    }

    def __init__(self, po_repository: PORepository) -> None:
        self._po_repository = po_repository

    def execute(
        self,
        tool_input: dict[str, Any],
    ) -> PurchaseOrder | None:
        po_id = str(tool_input["poId"])
        return self._po_repository.find_by_id(po_id)