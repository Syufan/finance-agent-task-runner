from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.evaluation.analyzer import analyze_traces


class EvaluationAnalyzerTestCase(unittest.TestCase):
    def test_analyze_traces_matches_task_example(self) -> None:
        traces = [
            {
                "traceId": "t1",
                "steps": [
                    {
                        "toolName": "invoice_lookup",
                        "status": "success",
                        "durationMs": 30,
                    },
                    {
                        "toolName": "po_lookup",
                        "status": "success",
                        "durationMs": 50,
                    },
                    {
                        "toolName": "policy_lookup",
                        "status": "failed",
                        "durationMs": 20,
                    },
                ],
            },
            {
                "traceId": "t2",
                "steps": [
                    {
                        "toolName": "invoice_lookup",
                        "status": "success",
                        "durationMs": 10,
                    },
                    {
                        "toolName": "policy_lookup",
                        "status": "success",
                        "durationMs": 40,
                    },
                ],
            },
        ]

        report = analyze_traces(traces)

        self.assertEqual(
            report,
            {
                "totalTraces": 2,
                "successTraces": 1,
                "failedTraces": 1,
                "averageDurationMs": 75,
                "toolStats": {
                    "invoice_lookup": {
                        "count": 2,
                        "success": 2,
                        "failed": 0,
                        "averageDurationMs": 20,
                    },
                    "po_lookup": {
                        "count": 1,
                        "success": 1,
                        "failed": 0,
                        "averageDurationMs": 50,
                    },
                    "policy_lookup": {
                        "count": 2,
                        "success": 1,
                        "failed": 1,
                        "averageDurationMs": 30,
                    },
                },
            },
        )

    def test_analyze_traces_returns_zeroed_report_for_empty_trace_list(self) -> None:
        report = analyze_traces([])

        self.assertEqual(
            report,
            {
                "totalTraces": 0,
                "successTraces": 0,
                "failedTraces": 0,
                "averageDurationMs": 0,
                "toolStats": {},
            },
        )

    def test_trace_with_empty_steps_counts_only_as_total_trace(self) -> None:
        report = analyze_traces(
            [
                {
                    "traceId": "t-empty",
                    "steps": [],
                }
            ]
        )

        self.assertEqual(report["totalTraces"], 1)
        self.assertEqual(report["successTraces"], 0)
        self.assertEqual(report["failedTraces"], 0)
        self.assertEqual(report["averageDurationMs"], 0)
        self.assertEqual(report["toolStats"], {})

    def test_missing_duration_ms_is_treated_as_zero(self) -> None:
        report = analyze_traces(
            [
                {
                    "traceId": "t1",
                    "steps": [
                        {
                            "toolName": "invoice_lookup",
                            "status": "success",
                        }
                    ],
                }
            ]
        )

        self.assertEqual(report["successTraces"], 1)
        self.assertEqual(report["averageDurationMs"], 0)
        self.assertEqual(
            report["toolStats"]["invoice_lookup"],
            {
                "count": 1,
                "success": 1,
                "failed": 0,
                "averageDurationMs": 0,
            },
        )

    def test_missing_tool_name_is_excluded_from_tool_stats_but_failed_status_fails_trace(self) -> None:
        report = analyze_traces(
            [
                {
                    "traceId": "t1",
                    "steps": [
                        {
                            "status": "failed",
                            "durationMs": 15,
                        }
                    ],
                }
            ]
        )

        self.assertEqual(report["failedTraces"], 1)
        self.assertEqual(report["toolStats"], {})
        self.assertEqual(report["averageDurationMs"], 15)

    def test_unknown_status_does_not_count_as_success_or_failed_step(self) -> None:
        report = analyze_traces(
            [
                {
                    "traceId": "t1",
                    "steps": [
                        {
                            "toolName": "invoice_lookup",
                            "status": "pending",
                            "durationMs": 10,
                        }
                    ],
                }
            ]
        )

        self.assertEqual(report["totalTraces"], 1)
        self.assertEqual(report["successTraces"], 0)
        self.assertEqual(report["failedTraces"], 0)
        self.assertEqual(
            report["toolStats"]["invoice_lookup"],
            {
                "count": 1,
                "success": 0,
                "failed": 0,
                "averageDurationMs": 10,
            },
        )


if __name__ == "__main__":
    unittest.main()
