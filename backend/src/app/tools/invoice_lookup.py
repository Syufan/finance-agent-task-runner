from typing import Any

from app.domain.models import Invoice
from app.repositories.invoice_repository import InvoiceRepository
from app.tools.base import Tool


class InvoiceLookupTool(Tool):
    name = "invoice_lookup"
    description = "Look up an invoice by invoice ID."
    input_schema = {
        "invoiceId": "string",
    }

    def __init__(self, invoice_repository: InvoiceRepository) -> None:
        self._invoice_repository = invoice_repository

    def execute(
        self,
        tool_input: dict[str, Any],
    ) -> Invoice | None:
        invoice_id = str(tool_input["invoiceId"])
        return self._invoice_repository.find_by_id(invoice_id)