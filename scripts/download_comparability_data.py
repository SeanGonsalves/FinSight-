"""Acquire supplementary adjusted Indian prices and USD/INR rates from Yahoo."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finsight.acquisition import download_comparability_data  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2016-01-01")
    parser.add_argument("--end", default="2026-01-01", help="Exclusive end date.")
    args = parser.parse_args()
    india_paths, fx_path = download_comparability_data(
        ROOT / "data" / "raw" / "india" / "yahoo_adjusted",
        ROOT / "data" / "raw" / "macroeconomic" / "usdinr_yahoo_2016_2025.parquet",
        start=args.start,
        end=args.end,
    )
    for path in india_paths:
        print(path)
    print(fx_path)


if __name__ == "__main__":
    main()
