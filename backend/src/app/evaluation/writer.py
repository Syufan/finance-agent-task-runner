import json
from pathlib import Path
from typing import Any


def serialize_evaluation_report(report: dict[str, Any]) -> str:
    """Serialize one evaluation report as formatted JSON."""
    if not isinstance(report, dict):
        raise ValueError("Evaluation report must be a dictionary.")

    return json.dumps(report, ensure_ascii=True, indent=2)


def write_evaluation_report(report: dict[str, Any], output_path: Path) -> Path:
    """Write one aggregated evaluation report to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialize_evaluation_report(report), encoding="utf-8")
    return output_path
