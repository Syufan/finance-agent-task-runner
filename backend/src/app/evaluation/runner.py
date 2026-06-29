from pathlib import Path
from typing import Any
from typing import Callable

from app.evaluation.analyzer import analyze_traces
from app.evaluation.loader import load_traces
from app.evaluation.writer import write_evaluation_report


def run_trace_evaluation(
    trace_directory: Path,
    output_path: Path,
    trace_loader: Callable[[Path], list[dict[str, Any]]] = load_traces,
    trace_analyzer: Callable[[list[dict[str, Any]]], dict[str, Any]] = analyze_traces,
    report_writer: Callable[[dict[str, Any], Path], None] = write_evaluation_report,
) -> dict[str, Any]:
    """Run the trace evaluation pipeline from load to write."""
    traces = trace_loader(trace_directory)
    report = trace_analyzer(traces)
    report_writer(report, output_path)
    return report
