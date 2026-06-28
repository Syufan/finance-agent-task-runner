from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionType(str, Enum):
    ASK_CLARIFICATION = "ask_clarification"
    RETURN_VALIDATION_ERROR = "return_validation_error"
    CALL_TOOL = "call_tool"
    STOP_WITH_ERROR = "stop_with_error"
    FINISH = "finish"
    FINISH_WITH_PARTIAL_ANSWER = "finish_with_partial_answer"


@dataclass
class NextAction:
    type: ActionType
    tool_name: str | None = None
    tool_input: dict | None = None
    message: str | None = None


class Planner:
    def decide(self, context):
        pass


# if no invoice ID was extracted:
#     ASK_CLARIFICATION

# elif invoice ID format is invalid:
#     RETURN_VALIDATION_ERROR

# elif invoice has not been looked up:
#     CALL invoice_lookup

# elif invoice lookup failed:
#     STOP_WITH_ERROR

# elif invoice was not found:
#     STOP_WITH_ERROR

# elif invoice.status == paid:
#     FINISH

# elif invoice has poId and PO has not been looked up:
#     CALL po_lookup

# elif PO lookup failed:
#     STOP_WITH_ERROR

# elif invoice has blockReason and policy has not been looked up:
#     CALL policy_lookup

# elif policy lookup failed or policy was not found:
#     FINISH_WITH_PARTIAL_ANSWER

# elif invoice.status in {blocked, pending_approval}:
#     FINISH

# else:
#     STOP_WITH_ERROR
