from __future__ import annotations

from app.tools.base import Tool


class InvoiceLookupTool(Tool):
    name = "invoice_lookup"

    def __init__(self, repository) -> None:
        self._repository = repository
