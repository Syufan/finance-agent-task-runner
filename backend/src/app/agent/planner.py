from dataclasses import dataclass
from enum import Enum

from app.agent.context import AgentContext, LookupState
from app.agent.errors import AgentError


class ActionType(str, Enum):
    ASK_CLARIFICATION = "ask_clarification"
    CALL_TOOL = "call_tool"
    FINISH = "finish"


@dataclass
class NextAction:
    type: ActionType
    tool_name: str | None = None
    tool_input: dict[str, object] | None = None
    message: str | None = None
    error: AgentError | None = None


class Planner:
    """
    Reads the current AgentContext and decides the next workflow action.

    The planner does not:
    - call tools
    - update context
    - write trace records
    - parse or validate invoice IDs
    """

    def decide(self, context: AgentContext) -> NextAction:
        # 1. Missing invoice ID:
        # No tools should be called.
        if context.invoice_id is None:
            return NextAction(
                type=ActionType.ASK_CLARIFICATION,
                message=(
                    "Please provide a valid invoice ID, "
                    "for example INV-1001."
                ),
            )

        # 2. Previous tool execution failure.
        # Policy failure is special: return a partial answer instead of failing.
        if context.error is not None:
            if context.error.source == "policy_lookup":
                return NextAction(
                    type=ActionType.FINISH,
                    message=(
                        "Policy information is unavailable. "
                        "Returning a partial answer based on the available "
                        "invoice and purchase order information."
                    ),
                )

            return NextAction(
                type=ActionType.FINISH,
                error=context.error,
            )

        # 3. Invoice has not been looked up yet.
        if context.invoice_lookup_state == LookupState.NOT_STARTED:
            return NextAction(
                type=ActionType.CALL_TOOL,
                tool_name="invoice_lookup",
                tool_input={"invoiceId": context.invoice_id},
            )

        # 4. Invoice lookup completed normally, but found no record.
        if context.invoice_lookup_state == LookupState.NOT_FOUND:
            return NextAction(
                type=ActionType.FINISH,
                error=AgentError(
                    code="INVOICE_NOT_FOUND",
                    message=f"Invoice {context.invoice_id} was not found.",
                    source="invoice_lookup",
                ),
            )

        # 5. Guard against impossible internal state.
        if context.invoice is None:
            return NextAction(
                type=ActionType.FINISH,
                error=AgentError(
                    code="INCONSISTENT_WORKFLOW_STATE",
                    message=(
                        "Invoice lookup completed without an invoice result."
                    ),
                    source="planner",
                ),
            )

        invoice = context.invoice

        # 6. Paid invoices require no further investigation.
        if invoice.status == "paid":
            return NextAction(type=ActionType.FINISH)

        # 7. A blocked or pending invoice with a PO needs PO investigation.
        if (
            invoice.poId is not None
            and context.po_lookup_state == LookupState.NOT_STARTED
        ):
            return NextAction(
                type=ActionType.CALL_TOOL,
                tool_name="po_lookup",
                tool_input={"poId": invoice.poId},
            )

        # 8. PO was requested but not found.
        if (
            invoice.poId is not None
            and context.po_lookup_state == LookupState.NOT_FOUND
        ):
            return NextAction(
                type=ActionType.FINISH,
                error=AgentError(
                    code="PURCHASE_ORDER_NOT_FOUND",
                    message=(
                        f"Purchase order {invoice.poId} was not found."
                    ),
                    source="po_lookup",
                ),
            )

        # 9. A block reason requires a policy lookup.
        if (
            invoice.blockReason is not None
            and context.policy_lookup_state == LookupState.NOT_STARTED
        ):
            return NextAction(
                type=ActionType.CALL_TOOL,
                tool_name="policy_lookup",
                tool_input={"blockReason": invoice.blockReason},
            )

        # 10. Policy lookup completed normally, but no matching policy exists.
        if context.policy_lookup_state == LookupState.NOT_FOUND:
            return NextAction(
                type=ActionType.FINISH,
                message=(
                    f"No policy was found for '{invoice.blockReason}'. "
                    "Returning a partial answer; please verify the policy "
                    "manually."
                ),
            )

        # 11. Enough information has been gathered.
        if invoice.status in {"blocked", "pending_approval"}:
            return NextAction(type=ActionType.FINISH)

        # 12. Any unrecognised state is treated as a controlled failure.
        return NextAction(
            type=ActionType.FINISH,
            error=AgentError(
                code="UNEXPECTED_WORKFLOW_STATE",
                message="The invoice workflow reached an unexpected state.",
                source="planner",
            ),
        )