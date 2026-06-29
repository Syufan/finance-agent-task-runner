from dataclasses import dataclass
from enum import Enum

class ErrorCode(str, Enum):
    MISSING_INVOICE_ID = "MISSING_INVOICE_ID"
    INVALID_INVOICE_ID = "INVALID_INVOICE_ID"
    INVOICE_NOT_FOUND = "INVOICE_NOT_FOUND"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    POLICY_NOT_FOUND = "POLICY_NOT_FOUND"

@dataclass
class AgentError:
    code: str
    message: str
    source: str | None = None
