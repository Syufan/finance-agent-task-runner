from __future__ import annotations

from app.data.json_data_source import JsonDataSource


class PORepository:
    def __init__(self, data_source: JsonDataSource) -> None:
        self._data_source = data_source

    def list_all(self) -> list[dict]:
        return self._data_source.load("pruchase_orders.json")
