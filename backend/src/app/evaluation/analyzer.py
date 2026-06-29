from typing import Any


def analyze_traces(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze a list of traces and return an aggregated report."""
    total_trace_duration = 0
    success_traces = 0
    failed_traces = 0
    tool_stats: dict[str, dict[str, int]] = {}

    for trace in traces:
        steps = _normalize_steps(trace)
        trace_duration = 0
        trace_has_failed_step = False
        trace_has_unknown_step = False

        for step in steps:
            duration_ms = _normalize_duration(step)
            status = _normalize_status(step)
            tool_name = _normalize_tool_name(step)

            trace_duration += duration_ms

            if status == "failed":
                trace_has_failed_step = True
            elif status != "success":
                trace_has_unknown_step = True

            if tool_name is None:
                continue

            stats = tool_stats.setdefault(
                tool_name,
                {
                    "count": 0,
                    "success": 0,
                    "failed": 0,
                    "totalDurationMs": 0,
                },
            )
            stats["count"] += 1
            stats["totalDurationMs"] += duration_ms

            if status == "success":
                stats["success"] += 1
            elif status == "failed":
                stats["failed"] += 1

        total_trace_duration += trace_duration

        if trace_has_failed_step:
            failed_traces += 1
        elif steps and not trace_has_unknown_step:
            success_traces += 1

    total_traces = len(traces)

    return {
        "totalTraces": total_traces,
        "successTraces": success_traces,
        "failedTraces": failed_traces,
        "averageDurationMs": (
            total_trace_duration // total_traces
            if total_traces
            else 0
        ),
        "toolStats": {
            tool_name: {
                "count": stats["count"],
                "success": stats["success"],
                "failed": stats["failed"],
                "averageDurationMs": (
                    stats["totalDurationMs"] // stats["count"]
                    if stats["count"]
                    else 0
                ),
            }
            for tool_name, stats in tool_stats.items()
        },
    }


def _normalize_steps(trace: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a safe step list from one trace."""
    steps = trace.get("steps", [])
    if not isinstance(steps, list):
        return []

    return [step for step in steps if isinstance(step, dict)]


def _normalize_duration(step: dict[str, Any]) -> int:
    """Return a safe step duration in milliseconds."""
    duration_ms = step.get("durationMs", 0)
    if not isinstance(duration_ms, int) or duration_ms < 0:
        return 0

    return duration_ms


def _normalize_tool_name(step: dict[str, Any]) -> str | None:
    """Return a safe tool name for aggregation."""
    tool_name = step.get("toolName")
    if not isinstance(tool_name, str):
        return None

    normalized = tool_name.strip()
    return normalized or None


def _normalize_status(step: dict[str, Any]) -> str:
    """Return a normalized step status."""
    status = step.get("status")
    if not isinstance(status, str):
        return "unknown"

    normalized = status.strip().lower()
    if normalized in {"success", "failed"}:
        return normalized

    return "unknown"
