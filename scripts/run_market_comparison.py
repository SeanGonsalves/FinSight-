"""Compare adjusted selected-stock histories in local currency and USD."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finsight.comparison import load_adjusted_comparison_data, write_comparison_outputs  # noqa: E402


def main() -> None:
    macro_path = ROOT / "data" / "raw" / "macroeconomic" / "world_bank_annual_2016_2025.parquet"
    prices = load_adjusted_comparison_data(
        ROOT / "data" / "raw" / "india" / "yahoo_adjusted",
        ROOT / "data" / "raw" / "usa" / "stocks",
        ROOT / "data" / "raw" / "macroeconomic" / "usdinr_yahoo_2016_2025.parquet",
    )
    outputs = write_comparison_outputs(
        prices,
        ROOT / "reports" / "tables",
        ROOT / "reports" / "figures" / "performance",
        ROOT / "reports" / "comparative_market_report.md",
        macro_data=pd.read_parquet(macro_path) if macro_path.exists() else None,
    )
    for label, path in outputs.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
