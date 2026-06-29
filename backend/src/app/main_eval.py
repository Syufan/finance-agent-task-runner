import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.evaluation.runner import run_trace_evaluation


DEFAULT_TRACE_DIRECTORY = Path(__file__).parent / "data" / "traces"


def main() -> None:
    """Run trace evaluation from the command line."""
    args = _parse_args()
    report = run_trace_evaluation(
        trace_directory=args.trace_dir,
        output_path=args.output,
    )
    print(f"Loaded traces from: {args.trace_dir}")
    print(f"Wrote evaluation report to: {args.output}")
    print(f"Total traces: {report['totalTraces']}")


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments for trace evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate persisted agent traces.")
    parser.add_argument(
        "--trace-dir",
        type=Path,
        default=DEFAULT_TRACE_DIRECTORY,
        help="Directory containing trace JSON files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_default_report_path(),
        help="Path to write the evaluation report JSON.",
    )
    return parser.parse_args()


def _default_report_path() -> Path:
    """Build a timestamped default output path for one evaluation run."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return (
        Path(__file__).parent
        / "data"
        / "evaluation"
        / f"report-{timestamp}.json"
    )


if __name__ == "__main__":
    main()
