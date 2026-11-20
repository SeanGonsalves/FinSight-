"""Explicit, reproducible acquisition of US equity data from Yahoo Finance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd

US_TICKERS = ("AAPL", "MSFT", "NVDA", "AMZN", "JPM", "WMT", "XOM", "TSLA", "JNJ", "BAC")
INDIA_COMPARISON_TICKERS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS",
    "ITC": "ITC.NS",
    "ONGC": "ONGC.NS",
    "WIPRO": "WIPRO.NS",
}
REQUIRED_US_COLUMNS = {"open", "high", "low", "close", "volume"}


def _flatten_yfinance_columns(columns: pd.Index, ticker: str) -> list[str]:
    if not isinstance(columns, pd.MultiIndex):
        return [str(column) for column in columns]
    for level in range(columns.nlevels):
        values = set(columns.get_level_values(level))
        if values == {ticker}:
            return [str(column) for column in columns.droplevel(level)]
    return [str(column[0]) for column in columns]


def download_us_history(
    output_dir: Path | str,
    *,
    tickers: Iterable[str] = US_TICKERS,
    start: str = "2016-01-01",
    end: str = "2026-01-01",
) -> list[Path]:
    """Download unadjusted OHLC plus adjusted close and actions, one file per ticker."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("Install yfinance from requirements.txt to download US data") from exc

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    tickers = tuple(tickers)
    completed: list[Path] = []
    failures: list[str] = []
    for ticker in tickers:
        try:
            frame = yf.download(
                ticker,
                start=start,
                end=end,
                auto_adjust=False,
                actions=True,
                progress=False,
                threads=False,
                group_by="column",
            )
            if frame.empty:
                raise ValueError("Yahoo Finance returned no rows")
            frame.columns = _flatten_yfinance_columns(frame.columns, ticker)
            frame = frame.rename(
                columns={
                    "Adj Close": "adj_close",
                    "Stock Splits": "stock_splits",
                    "Dividends": "dividends",
                }
            )
            frame = frame.rename(columns={column: str(column).lower() for column in frame.columns})
            frame.index.name = "date"
            frame = frame.reset_index()
            frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.tz_localize(None)
            frame["symbol"] = ticker
            frame["market"] = "USA"
            frame["currency"] = "USD"
            missing = REQUIRED_US_COLUMNS.difference(frame.columns)
            if missing:
                raise ValueError(f"response missing columns: {sorted(missing)}")
            if frame[list(REQUIRED_US_COLUMNS)].isna().all(axis=None):
                raise ValueError("response contains no usable OHLCV values")

            path = destination / f"usa_{ticker.lower()}_2016_2025.parquet"
            frame.to_parquet(path, index=False)
            completed.append(path)
        except Exception as exc:
            failures.append(f"{ticker}: {type(exc).__name__}: {exc}")

    if failures:
        raise RuntimeError(
            "One or more US ticker downloads failed. "
            f"Completed {len(completed)} of {len(tuple(tickers))}; details: {'; '.join(failures)}"
        )
    return completed


def _download_yahoo_frame(ticker: str, start: str, end: str) -> pd.DataFrame:
    import yfinance as yf

    frame = yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=False,
        actions=True,
        progress=False,
        threads=False,
        group_by="column",
    )
    if frame.empty:
        raise ValueError("Yahoo Finance returned no rows")
    frame.columns = _flatten_yfinance_columns(frame.columns, ticker)
    frame = frame.rename(
        columns={
            "Adj Close": "adj_close",
            "Stock Splits": "stock_splits",
            "Dividends": "dividends",
        }
    )
    frame = frame.rename(columns={column: str(column).lower() for column in frame.columns})
    frame.index.name = "date"
    frame = frame.reset_index()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.tz_localize(None)
    if frame["date"].duplicated().any():
        raise ValueError("Yahoo Finance returned duplicate dates")
    return frame


def download_comparability_data(
    india_output_dir: Path | str,
    fx_output_path: Path | str,
    *,
    start: str = "2016-01-01",
    end: str = "2026-01-01",
) -> tuple[list[Path], Path]:
    """Fetch Yahoo adjusted closes for comparable Indian stocks and USD/INR."""
    try:
        import yfinance  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Install yfinance from requirements.txt to download comparison data") from exc

    india_dir = Path(india_output_dir)
    fx_path = Path(fx_output_path)
    india_dir.mkdir(parents=True, exist_ok=True)
    fx_path.parent.mkdir(parents=True, exist_ok=True)
    completed: list[Path] = []
    failures: list[str] = []

    for symbol, ticker in INDIA_COMPARISON_TICKERS.items():
        try:
            frame = _download_yahoo_frame(ticker, start, end)
            if "adj_close" not in frame or frame["adj_close"].isna().any():
                raise ValueError("response has no complete adjusted-close history")
            if (frame["adj_close"] <= 0).any():
                raise ValueError("response contains nonpositive adjusted closes")
            frame["symbol"] = symbol
            frame["source_ticker"] = ticker
            frame["market"] = "INDIA"
            frame["currency"] = "INR"
            path = india_dir / f"india_yahoo_{symbol.lower()}_2016_2025.parquet"
            frame.to_parquet(path, index=False)
            completed.append(path)
        except Exception as exc:
            failures.append(f"{ticker}: {type(exc).__name__}: {exc}")

    try:
        fx = _download_yahoo_frame("USDINR=X", start, end)
        if "close" not in fx or fx["close"].isna().any() or (fx["close"] <= 0).any():
            raise ValueError("USDINR=X returned missing or nonpositive rates")
        fx["symbol"] = "USDINR"
        fx["source_ticker"] = "USDINR=X"
        fx["market"] = "FX"
        fx["currency"] = "INR per USD"
        fx.to_parquet(fx_path, index=False)
    except Exception as exc:
        failures.append(f"USDINR=X: {type(exc).__name__}: {exc}")

    if failures:
        raise RuntimeError(
            "One or more comparison-data downloads failed. "
            f"Completed {len(completed)} of {len(INDIA_COMPARISON_TICKERS)} Indian tickers; "
            f"details: {'; '.join(failures)}"
        )
    return completed, fx_path


def download_world_bank_macro(
    output_path: Path | str,
    *,
    start_year: int = 2016,
    end_year: int = 2025,
) -> Path:
    """Download annual CPI inflation and GDP growth for India and the USA."""
    indicators = {
        "FP.CPI.TOTL.ZG": "Inflation, consumer prices (annual %)",
        "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    }
    countries = "IND;USA"
    records: list[dict[str, object]] = []
    retrieved_at = pd.Timestamp.now(tz="UTC")

    for indicator, indicator_name in indicators.items():
        country_path = quote(countries, safe="")
        url = (
            f"https://api.worldbank.org/v2/country/{country_path}/indicator/{indicator}"
            f"?date={start_year}:{end_year}&format=json&per_page=100"
        )
        request = Request(url, headers={"User-Agent": "FinSight-academic-research/0.1"})
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.load(response)
        except Exception as exc:
            raise RuntimeError(f"World Bank request failed for {indicator}: {exc}") from exc
        if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
            raise ValueError(f"Unexpected World Bank response for {indicator}")
        source_updated = payload[0].get("lastupdated")
        for observation in payload[1]:
            records.append(
                {
                    "country_code": observation.get("countryiso3code"),
                    "country": observation.get("country", {}).get("value"),
                    "year": int(observation["date"]),
                    "indicator_code": indicator,
                    "indicator": indicator_name,
                    "value": observation.get("value"),
                    "unit": observation.get("unit"),
                    "source_last_updated": source_updated,
                    "retrieved_at_utc": retrieved_at,
                }
            )

    frame = pd.DataFrame(records)
    if frame.empty or frame.duplicated(["country_code", "year", "indicator_code"]).any():
        raise ValueError("World Bank response was empty or had duplicate country/year/indicator rows")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    return output
