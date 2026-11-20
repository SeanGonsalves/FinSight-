"""Download annual World Bank CPI and GDP growth for India and the USA."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finsight.acquisition import download_world_bank_macro  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2016)
    parser.add_argument("--end-year", type=int, default=2025)
    args = parser.parse_args()
    path = download_world_bank_macro(
        ROOT / "data" / "raw" / "macroeconomic" / "world_bank_annual_2016_2025.parquet",
        start_year=args.start_year,
        end_year=args.end_year,
    )
    print(path)


if __name__ == "__main__":
    main()
