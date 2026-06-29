from app.data.json_data_source import JsonDataSource
from app.domain.models import Invoice


class InvoiceRepository:
    def __init__(self, data_source: JsonDataSource) -> None:
        self._data_source = data_source

    def find_by_id(self, invoice_id: str) -> Invoice | None:
        invoices = self._data_source.load("invoices.json")

        for item in invoices:
            if item["invoiceId"] == invoice_id:
                return Invoice(
                    invoiceId=item["invoiceId"],
                    vendor=item["vendor"],
                    amount=item["amount"],
                    currency=item["currency"],
                    status=item["status"],
                    poId=item["poId"],
                    blockReason=item["blockReason"],
                )

        return None