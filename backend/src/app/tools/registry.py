from __future__ import annotations


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, object] = {}

    def register(self, tool) -> None:
        tool_name = getattr(tool, "name", tool.__class__.__name__)
        self._tools[tool_name] = tool

    def get(self, tool_name: str):
        return self._tools.get(tool_name)
