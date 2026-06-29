from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    name: str
    description: str
    input_schema: dict[str, str]

    @abstractmethod
    def execute(self, tool_input: dict[str, Any]) -> object | None:
        """Run the tool."""