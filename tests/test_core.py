from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from finsight.acquisition import download_us_history
from finsight.comparison import build_macro_correlations, load_adjusted_comparison_data
from finsight.data import validate_ohlc
from finsight.indicators import add_technical_indicators
from finsight.metrics import daily_returns, risk_performance_summary
from finsight.modeling import make_next_return_features


class MetricsTests(unittest.TestCase):
    def test_daily_returns_are_grouped_and_ordered(self) -> None:
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(["2020-01-02", "2020-01-01", "2020-01-01"]),
                "symbol": ["A", "A", "B"],
                "close": [110.0, 100.0, 20.0],
            }
        )
        result = daily_returns(frame)
        returns_a = result.loc[result["symbol"].eq("A"), "daily_return"].tolist()
        self.assertTrue(pd.isna(returns_a[0]))
        self.assertAlmostEqual(returns_a[1], 0.1)

    def test_risk_summary_reports_drawdown_and_annualization(self) -> None:
        frame = pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=5),
                "symbol": ["A"] * 5,
                "close": [100.0, 110.0, 90.0, 95.0, 100.0],
            }
        )
        summary = risk_performance_summary(frame)
        self.assertEqual(len(summary), 1)
        self.assertLess(summary.loc[0, "max_drawdown"], 0)
        self.assertGreater(summary.loc[0, "annualized_volatility"], 0)


class ValidationAndIndicatorTests(unittest.TestCase):
    def test_ohlc_validation_rejects_high_below_close(self) -> None:
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(["2020-01-01"]),
                "symbol": ["A"],
                "series": ["EQ"],
                "open": [10.0],
                "high": [9.0],
                "low": [8.0],
                "close": [9.5],
                "volume": [1],
            }
        )
        with self.assertRaisesRegex(ValueError, "invalid OHLC"):
            validate_ohlc(frame, context="test")

    def test_sma_uses_only_current_and_prior_observations(self) -> None:
        frame = pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=21),
                "symbol": ["A"] * 21,
                "close": list(range(1, 22)),
            }
        )
        result = add_technical_indicators(frame)
        self.assertAlmostEqual(result.loc[19, "sma_20"], 10.5)
        self.assertAlmostEqual(result.loc[20, "sma_20"], 11.5)

    def test_forecast_target_is_next_observed_return(self) -> None:
        frame = pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=160),
                "symbol": ["A"] * 160,
                "close": [100.0 + index for index in range(160)],
                "volume": [1000 + index for index in range(160)],
            }
        )
        features, _ = make_next_return_features(frame)
        first = features.iloc[0]
        self.assertEqual(first["target_date"], pd.Timestamp("2020-02-20"))
        self.assertAlmostEqual(first["target_return"], 1.0 / 149.0)

    def test_us_download_preserves_adjusted_close_and_actions(self) -> None:
        columns = pd.MultiIndex.from_tuples(
            [
                ("Open", "XYZ"),
                ("High", "XYZ"),
                ("Low", "XYZ"),
                ("Close", "XYZ"),
                ("Adj Close", "XYZ"),
                ("Volume", "XYZ"),
                ("Dividends", "XYZ"),
                ("Stock Splits", "XYZ"),
            ]
        )
        response = pd.DataFrame(
            [[10.0, 12.0, 9.0, 11.0, 10.5, 1000, 0.1, 0.0]],
            index=pd.DatetimeIndex(["2020-01-02"]),
            columns=columns,
        )
        with tempfile.TemporaryDirectory() as directory:
            with patch("yfinance.download", return_value=response) as download:
                paths = download_us_history(directory, tickers=["XYZ"])
            result = pd.read_parquet(paths[0])

        download.assert_called_once()
        self.assertFalse(download.call_args.kwargs["auto_adjust"])
        self.assertTrue(download.call_args.kwargs["actions"])
        self.assertIn("adj_close", result.columns)
        self.assertIn("dividends", result.columns)
        self.assertIn("stock_splits", result.columns)
        self.assertEqual(result.loc[0, "currency"], "USD")

    def test_indian_usd_conversion_uses_strictly_prior_fx_date(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            india_dir = root / "india"
            usa_dir = root / "usa"
            india_dir.mkdir()
            usa_dir.mkdir()
            dates = pd.to_datetime(["2020-01-02", "2020-01-03"])
            pd.DataFrame(
                {
                    "date": dates,
                    "symbol": ["RELIANCE", "RELIANCE"],
                    "adj_close": [110.0, 120.0],
                }
            ).to_parquet(india_dir / "india_yahoo_reliance_2016_2025.parquet", index=False)
            pd.DataFrame(
                {
                    "date": dates,
                    "symbol": ["AAPL", "AAPL"],
                    "adj_close": [10.0, 11.0],
                }
            ).to_parquet(usa_dir / "usa_aapl_2016_2025.parquet", index=False)
            fx_path = root / "fx.parquet"
            pd.DataFrame(
                {
                    "date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
                    "close": [10.0, 11.0, 12.0],
                }
            ).to_parquet(fx_path, index=False)

            result = load_adjusted_comparison_data(india_dir, usa_dir, fx_path)
            india = result.loc[result["market"].eq("INDIA")].sort_values("date")

        self.assertEqual(india["inr_per_usd"].tolist(), [10.0, 11.0])
        self.assertEqual(india["adj_close_usd"].tolist(), [11.0, 120.0 / 11.0])

    def test_macro_correlations_align_by_country_and_year(self) -> None:
        market_daily = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2020-12-30",
                        "2020-12-31",
                        "2021-12-30",
                        "2021-12-31",
                        "2022-12-30",
                        "2022-12-31",
                    ]
                ),
                "market": ["INDIA", "USA"] * 3,
                "local_return": [0.1, 0.2, 0.2, 0.1, -0.1, 0.3],
            }
        )
        macro = pd.DataFrame(
            {
                "country_code": ["IND", "IND", "IND", "USA", "USA", "USA"],
                "year": [2020, 2021, 2022] * 2,
                "indicator_code": ["FP.CPI.TOTL.ZG"] * 6,
                "value": [1.0, 2.0, 3.0, 3.0, 2.0, 1.0],
            }
        )

        annual, correlations = build_macro_correlations(market_daily, macro)

        self.assertEqual(len(annual), 6)
        self.assertEqual(len(correlations), 2)
        self.assertEqual(set(correlations["observations"]), {3})


if __name__ == "__main__":
    unittest.main()
