import json
from pathlib import Path
from typing import Any


def list_trace_files(trace_directory: Path) -> list[Path]:
    """Return sorted trace JSON files from the trace directory."""
    if not trace_directory.exists():
        return []

    return sorted(
        trace_file
        for trace_file in trace_directory.glob("*.json")
        if trace_file.is_file()
    )


def load_trace_file(trace_path: Path) -> dict[str, Any]:
    """Load one trace JSON file."""
    payload = json.loads(trace_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError(f"Trace file must contain one JSON object: {trace_path}")

    payload.setdefault("traceId", trace_path.stem)
    payload.setdefault("steps", [])

    if not isinstance(payload["steps"], list):
        raise ValueError(f"Trace steps must be a list: {trace_path}")

    return payload


def load_traces(trace_directory: Path) -> list[dict[str, Any]]:
    """Load every trace JSON file from a directory."""
    return [
        load_trace_file(trace_path)
        for trace_path in list_trace_files(trace_directory)
    ]
