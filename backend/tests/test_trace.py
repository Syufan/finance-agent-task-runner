from datetime import datetime
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.agent.trace import AgentTrace, TraceStep, TraceStore


class TraceTestCase(unittest.TestCase):
    def test_agent_trace_has_trace_id_after_creation(self) -> None:
        trace = AgentTrace(userRequest="Check invoice INV-1001")

        self.assertIsInstance(trace.traceId, str)
        self.assertNotEqual(trace.traceId, "")

    def test_trace_store_returns_saved_trace(self) -> None:
        trace_store = TraceStore()
        trace = AgentTrace(userRequest="Check invoice INV-1001")

        trace_store.save(trace)

        self.assertIs(trace_store.get(trace.traceId), trace)

    def test_trace_step_can_be_saved_in_trace_steps(self) -> None:
        trace_store = TraceStore()
        trace = AgentTrace(userRequest="Check invoice INV-1001")
        step = TraceStep(
            stepId="step-001",
            stepName="invoice_lookup",
            toolName="invoice_lookup",
            input={"invoiceId": "INV-1001"},
            output={"invoiceId": "INV-1001"},
            status="success",
            error=None,
            startedAt=datetime(2026, 6, 29, 10, 0, 0),
            durationMs=8,
        )

        trace.steps.append(step)
        trace_store.save(trace)
        saved_trace = trace_store.get(trace.traceId)

        self.assertIsNotNone(saved_trace)
        assert saved_trace is not None
        self.assertEqual(saved_trace.steps, [step])

    def test_get_returns_none_for_missing_trace_id(self) -> None:
        trace_store = TraceStore()

        self.assertIsNone(trace_store.get("trace-missing"))


if __name__ == "__main__":
    unittest.main()
