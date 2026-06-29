import re
import time
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.agent.context import AgentContext, LookupState
from app.agent.errors import AgentError
from app.agent.planner import ActionType, Planner
from app.agent.trace import AgentTrace, TraceStore
from app.tools.registry import ToolRegistry


INVOICE_ID_CANDIDATE_PATTERN = re.compile(
    r"\bINV-[A-Za-z0-9]+\b",
    re.IGNORECASE,
)

INVOICE_ID_PATTERN = re.compile(
    r"INV-\d{4}",
    re.IGNORECASE,
)


def _extract_invoice_id_candidate(user_request: str) -> str | None:
    """Find a possible invoice ID in the user request."""
    match = INVOICE_ID_CANDIDATE_PATTERN.search(user_request)
    return match.group(0).upper() if match else None


def _is_valid_invoice_id(invoice_id: str) -> bool:
    """Validate the invoice ID format."""
    return INVOICE_ID_PATTERN.fullmatch(invoice_id) is not None


@dataclass
class AgentRunResult:
    status: str
    finalAnswer: str
    actions: list[str]
    traceId: str
    error: AgentError | None = None


class AgentRunner:
    def __init__(
        self,
        planner: Planner,
        tool_registry: ToolRegistry,
        trace_store: TraceStore,
    ) -> None:
        self._planner = planner
        self._tool_registry = tool_registry
        self._trace_store = trace_store

    def run(self, user_request: str) -> AgentRunResult:
        """Run one agent workflow."""
        trace = AgentTrace(traceId=str(uuid4()),userRequest=user_request)
        self._trace_store.save(trace)
        actions: list[str] = []

        # Create a request-specific context and validate the invoice ID
        context, input_error = self._create_initial_context(user_request)

        # Stop early when the input is invalid.
        if input_error is not None:
            # Record the validation failure in the trace.
            self._record_trace_step(
                trace=trace,
                step_name="input_validation",
                tool_name=None,
                step_input={"userRequest": user_request},
                output={},
                status="failed",
                error=input_error.message,
                started_at=datetime.now(timezone.utc),
                duration_ms=0,
            )

            # Save the trace and return a failed result.
            return self._finish_with_message(
                trace=trace,
                actions=actions,
                status="failed",
                message=input_error.message,
            )

        assert context is not None

        while True:
            action = self._planner.decide(context)

            # Ask the user for missing information.
            if action.type == ActionType.ASK_CLARIFICATION:
                return self._finish_with_message(
                    trace=trace,
                    actions=actions,
                    status="needs_input",
                    message=action.message or "Please provide an invoice ID.",
                )

            # Return the final result.
            if action.type == ActionType.FINISH:
                # Return a failed result when the workflow ends with an error.
                if action.error is not None:
                    return self._finish_with_message(
                        trace=trace,
                        actions=actions,
                        status="failed",
                        message=action.error.message,
                    )

                # Return a completed result when the workflow ends normally.
                final_answer = self._build_final_answer(
                    context=context,
                    completion_message=action.message,
                )

                return self._finish_with_message(
                    trace=trace,
                    actions=actions,
                    status="completed",
                    message=final_answer,
                )

            # Run the requested tool, then decide again.
            if action.type == ActionType.CALL_TOOL:
                self._execute_tool_action(
                    context=context,
                    trace=trace,
                    actions=actions,
                    tool_name=action.tool_name,
                    tool_input=action.tool_input or {},
                )
                continue

            # Catch any action type that the Runner does not support.
            raise RuntimeError(f"Unsupported action type: {action.type}")

    def _create_initial_context(
        self,
        user_request: str,
    ) -> tuple[AgentContext | None, AgentError | None]:
        """Create the context for this request."""
        invoice_id = _extract_invoice_id_candidate(user_request)

        # No invoice ID found.
        if invoice_id is None:
            return AgentContext(invoice_id=None), None

        # A possible invoice ID exists, but it is invalid.
        if not _is_valid_invoice_id(invoice_id):
            return None, AgentError(
                code="INVALID_INVOICE_ID",
                message=(
                    f"Invoice ID '{invoice_id}' is invalid. "
                    "Expected format: INV-XXXX."
                ),
                source="input_parser",
            )

        return AgentContext(invoice_id=invoice_id), None

    def _execute_tool_action(
        self,
        context: AgentContext,
        trace: AgentTrace,
        actions: list[str],
        tool_name: str | None,
        tool_input: dict[str, Any],
    ) -> None:
        """Execute one tool call and update the context."""
        if tool_name is None:
            error = AgentError(
                code="MISSING_TOOL_NAME",
                message="Planner returned CALL_TOOL without a tool name.",
                source="runner",
            )
            context.error = error
            return

        actions.append(tool_name)

        started_at = datetime.now(timezone.utc)
        started_time = time.perf_counter()

        try:
            # 1. Find the requested tool from the registry.
            tool = self._tool_registry.get(tool_name)
            if tool is None:
                raise RuntimeError(f"Tool '{tool_name}' is not registered.")
            
            # 2. Run the tool and save its result in the current context.
            result = tool.execute(tool_input)
            
            self._apply_tool_result(
                context=context,
                tool_name=tool_name,
                result=result,
            )
            
            # 3. Record the tool call in the trace.
            self._record_trace_step(
                trace=trace,
                step_name=tool_name,
                tool_name=tool_name,
                step_input=tool_input,
                output=self._to_trace_output(result),
                status="success",
                error=None,
                started_at=started_at,
                duration_ms=self._duration_ms(started_time),
            )

        except Exception as exc:
            # 1. Convert the unexpected exception into a structured AgentError.
            error = AgentError(
                code="TOOL_EXECUTION_FAILED",
                message=f"Tool '{tool_name}' failed: {str(exc)}",
                source=tool_name,
            )

            # 2. Save the failure in Context so the Planner can decide what to do next.
            self._apply_tool_error(
                context=context,
                tool_name=tool_name,
                error=error,
            )

            # 3. Record the failed tool call in the trace.
            self._record_trace_step(
                trace=trace,
                step_name=tool_name,
                tool_name=tool_name,
                step_input=tool_input,
                output={},
                status="failed",
                error=error.message,
                started_at=started_at,
                duration_ms=self._duration_ms(started_time),
            )

    def _apply_tool_result(
        self,
        context: AgentContext,
        tool_name: str,
        result: Any,
    ) -> None:
        """Write the tool result back to the context."""
        if tool_name == "invoice_lookup":
            context.invoice = result
            context.invoice_lookup_state = (
                LookupState.FOUND
                if result is not None
                else LookupState.NOT_FOUND
            )
            return

        if tool_name == "po_lookup":
            context.purchase_order = result
            context.po_lookup_state = (
                LookupState.FOUND
                if result is not None
                else LookupState.NOT_FOUND
            )
            return

        if tool_name == "policy_lookup":
            context.policy = result
            context.policy_lookup_state = (
                LookupState.FOUND
                if result is not None
                else LookupState.NOT_FOUND
            )
            return

        context.error = AgentError(
            code="UNKNOWN_TOOL",
            message=f"Tool '{tool_name}' is not supported by the runner.",
            source="runner",
        )

    def _apply_tool_error(
        self,
        context: AgentContext,
        tool_name: str,
        error: AgentError,
    ) -> None:
        """Store a tool failure in the context."""
        context.error = error

        if tool_name == "invoice_lookup":
            context.invoice_lookup_state = LookupState.FAILED

        elif tool_name == "po_lookup":
            context.po_lookup_state = LookupState.FAILED

        elif tool_name == "policy_lookup":
            context.policy_lookup_state = LookupState.FAILED

    def _build_final_answer(
        self,
        context: AgentContext,
        completion_message: str | None,
    ) -> str:
        """Build the final user-facing answer from the completed context."""
        invoice = context.invoice

        if invoice is None:
            return completion_message or "The workflow completed without invoice details."

        invoice_amount = f"{invoice.currency} {invoice.amount:,.0f}"
        lines = [
            f"Invoice {invoice.invoiceId} for {invoice.vendor} "
            f"({invoice_amount}) has status: {invoice.status}.",
        ]

        if invoice.status == "paid":
            lines.append("No further action is required.")

        elif invoice.status == "blocked":
            if context.purchase_order is not None:
                purchase_order = context.purchase_order
                po_amount = (
                    f"{purchase_order.currency} "
                    f"{purchase_order.amount:,.0f}"
                )

                lines.append(
                    f"The invoice amount is {invoice_amount}, while "
                    f"purchase order {purchase_order.poId} is {po_amount}."
                )

                lines.append(
                    f"PO owner: {purchase_order.owner}."
                )

            if context.policy is not None:
                policy = context.policy

                lines.append(f"Policy: {policy.policy}")
                lines.append(
                    f"Recommended next step: {policy.recommendedAction}"
                )

        elif invoice.status == "pending_approval":
            lines.append("The invoice is waiting for approval.")

            if context.purchase_order is not None:
                lines.append(
                    f"PO owner: {context.purchase_order.owner}."
                )

            if context.policy is not None:
                policy = context.policy

                lines.append(f"Policy: {policy.policy}")
                lines.append(
                    f"Recommended next step: {policy.recommendedAction}"
                )

        if completion_message:
            lines.append(completion_message)

        return " ".join(lines)
    
    def _finish_with_message(
        self,
        trace: AgentTrace,
        actions: list[str],
        status: str,
        message: str,
    ) -> AgentRunResult:
        """Save the trace and return the final run result."""
        trace.finalAnswer = message
        self._trace_store.save(trace)
        return AgentRunResult(
            status=status,
            finalAnswer=message,
            actions=actions,
            traceId=trace.traceId,
        )

    def _record_trace_step(
        self,
        trace: AgentTrace,
        step_name: str,
        tool_name: str | None,
        step_input: dict[str, Any],
        output: dict[str, Any],
        status: str,
        error: str | None,
        started_at: datetime,
        duration_ms: int,
    ) -> None:
        """Add one execution step to the trace."""
        trace.steps.append(
            {
                "stepId": str(uuid4()),
                "stepName": step_name,
                "toolName": tool_name or "",
                "input": step_input,
                "output": output,
                "status": status,
                "error": error,
                "startedAt": started_at,
                "durationMs": duration_ms,
            }
        )
        self._trace_store.save(trace)

    @staticmethod
    def _duration_ms(started_time: float) -> int:
        """Return elapsed milliseconds."""
        return int((time.perf_counter() - started_time) * 1000)

    @staticmethod
    def _to_trace_output(result: Any) -> dict[str, Any]:
        """Convert a tool result into trace-friendly data."""
        if result is None:
            return {}

        if is_dataclass(result):
            return asdict(result)

        if isinstance(result, dict):
            return result

        return {"value": str(result)}
