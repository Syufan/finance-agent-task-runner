from app.data.json_data_source import JsonDataSource
from app.domain.models import PurchaseOrder


class PORepository:
    def __init__(self, data_source: JsonDataSource) -> None:
        self._data_source = data_source

    def find_by_id(self, po_id: str) -> PurchaseOrder | None:
        purchase_orders = self._data_source.load("purchase_orders.json")

        for item in purchase_orders:
            if item["poId"] == po_id:
                return PurchaseOrder(
                    poId=item["poId"],
                    amount=item["amount"],
                    currency=item["currency"],
                    owner=item["owner"],
                    status=item["status"],
                )

        return None
