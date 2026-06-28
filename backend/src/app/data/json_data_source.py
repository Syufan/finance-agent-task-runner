from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonDataSource:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir

    def load(self, filename: str) -> list[dict[str, Any]]:
        path = self._data_dir / filename
        with path.open(encoding="utf-8") as file:
            return json.load(file)
