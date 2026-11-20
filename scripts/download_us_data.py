"""Acquire requested US daily prices and corporate actions from Yahoo Finance."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finsight.acquisition import US_TICKERS, download_us_history  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2016-01-01")
    parser.add_argument("--end", default="2026-01-01", help="Exclusive end date.")
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=list(US_TICKERS),
        help="Yahoo Finance tickers to download.",
    )
    args = parser.parse_args()
    paths = download_us_history(
        ROOT / "data" / "raw" / "usa" / "stocks",
        tickers=args.tickers,
        start=args.start,
        end=args.end,
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
