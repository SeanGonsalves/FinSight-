"""Run the reproducible local India-only analysis pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finsight.pipeline import run_analysis  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="RELIANCE", help="Indian symbol to model.")
    parser.add_argument(
        "--overwrite-processed",
        action="store_true",
        help="Rebuild the combined EQ dataset from raw NSE files.",
    )
    args = parser.parse_args()
    outputs = run_analysis(
        ROOT,
        forecast_symbol=args.symbol,
        overwrite_processed=args.overwrite_processed,
    )
    for label, path in outputs.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
