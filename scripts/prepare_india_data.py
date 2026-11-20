"""Build the combined, validated Indian EQ-series dataset."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finsight.data import build_processed_india  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the processed output if it already exists.",
    )
    args = parser.parse_args()
    output = build_processed_india(
        ROOT / "data" / "raw" / "india" / "stocks",
        ROOT / "data" / "processed" / "india" / "eq_daily.parquet",
        overwrite=args.overwrite,
    )
    print(f"Processed Indian EQ data written to {output}")


if __name__ == "__main__":
    main()
