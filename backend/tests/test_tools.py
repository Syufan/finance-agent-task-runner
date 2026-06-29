from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.tools.base import Tool
from app.tools.registry import ToolRegistry


class ConcreteTool(Tool):
    name = "test_tool"
    description = "Test tool."
    input_schema = {"value": "string"}

    def execute(self, tool_input: dict[str, object]) -> object | None:
        return tool_input


class MissingExecuteTool(Tool):
    name = "missing_execute"
    description = "Missing execute."
    input_schema = {}


class ToolBaseAndRegistryTestCase(unittest.TestCase):
    def test_tool_requires_execute_implementation(self) -> None:
        with self.assertRaises(TypeError):
            MissingExecuteTool()

    def test_registry_returns_registered_tool(self) -> None:
        registry = ToolRegistry()
        tool = ConcreteTool()

        registry.register(tool)

        self.assertIs(registry.get("test_tool"), tool)

    def test_registry_returns_none_for_missing_tool(self) -> None:
        registry = ToolRegistry()

        self.assertIsNone(registry.get("missing_tool"))

    def test_registry_overwrites_existing_tool_with_same_name(self) -> None:
        registry = ToolRegistry()
        first = ConcreteTool()

        class ReplacementTool(ConcreteTool):
            pass

        second = ReplacementTool()

        registry.register(first)
        registry.register(second)

        self.assertIs(registry.get("test_tool"), second)


if __name__ == "__main__":
    unittest.main()
