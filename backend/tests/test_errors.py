from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.agent.errors import AgentError, ErrorCode


class ErrorsTestCase(unittest.TestCase):
    def test_error_code_exposes_expected_values(self) -> None:
        self.assertEqual(ErrorCode.MISSING_INVOICE_ID.value, "MISSING_INVOICE_ID")
        self.assertEqual(ErrorCode.INVALID_INVOICE_ID.value, "INVALID_INVOICE_ID")
        self.assertEqual(ErrorCode.INVOICE_NOT_FOUND.value, "INVOICE_NOT_FOUND")
        self.assertEqual(ErrorCode.TOOL_EXECUTION_FAILED.value, "TOOL_EXECUTION_FAILED")
        self.assertEqual(ErrorCode.POLICY_NOT_FOUND.value, "POLICY_NOT_FOUND")

    def test_agent_error_stores_code_message_and_source(self) -> None:
        error = AgentError(
            code=ErrorCode.INVALID_INVOICE_ID.value,
            message="Invoice ID format is invalid.",
            source="input_parser",
        )

        self.assertEqual(error.code, "INVALID_INVOICE_ID")
        self.assertEqual(error.message, "Invoice ID format is invalid.")
        self.assertEqual(error.source, "input_parser")

    def test_agent_error_source_is_optional(self) -> None:
        error = AgentError(
            code=ErrorCode.INVOICE_NOT_FOUND.value,
            message="Invoice INV-1001 was not found.",
        )

        self.assertEqual(error.code, "INVOICE_NOT_FOUND")
        self.assertEqual(error.message, "Invoice INV-1001 was not found.")
        self.assertIsNone(error.source)


if __name__ == "__main__":
    unittest.main()
