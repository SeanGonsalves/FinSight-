"""Descriptive technical indicators computed from historical prices."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_technical_indicators(
    frame: pd.DataFrame,
    *,
    rsi_window: int = 14,
    band_window: int = 20,
) -> pd.DataFrame:
    """Add SMA, EMA, RSI, MACD, and Bollinger columns without using future data."""
    required = {"date", "symbol", "close"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Required columns: {sorted(required)}")
    if rsi_window < 2 or band_window < 2:
        raise ValueError("Indicator windows must be at least 2")

    result = frame.sort_values(["symbol", "date"]).copy()
    grouped = result.groupby("symbol", sort=False)["close"]
    result["sma_20"] = grouped.transform(lambda values: values.rolling(20, min_periods=20).mean())
    result["sma_50"] = grouped.transform(lambda values: values.rolling(50, min_periods=50).mean())
    result["ema_12"] = grouped.transform(
        lambda values: values.ewm(span=12, adjust=False, min_periods=12).mean()
    )
    result["ema_26"] = grouped.transform(
        lambda values: values.ewm(span=26, adjust=False, min_periods=26).mean()
    )
    result["macd"] = result["ema_12"] - result["ema_26"]
    result["macd_signal"] = result.groupby("symbol", sort=False)["macd"].transform(
        lambda values: values.ewm(span=9, adjust=False, min_periods=9).mean()
    )
    result["macd_histogram"] = result["macd"] - result["macd_signal"]

    difference = result.groupby("symbol", sort=False)["close"].diff()
    gains = difference.clip(lower=0)
    losses = -difference.clip(upper=0)
    average_gain = gains.groupby(result["symbol"], sort=False).transform(
        lambda values: values.ewm(alpha=1 / rsi_window, adjust=False, min_periods=rsi_window).mean()
    )
    average_loss = losses.groupby(result["symbol"], sort=False).transform(
        lambda values: values.ewm(alpha=1 / rsi_window, adjust=False, min_periods=rsi_window).mean()
    )
    relative_strength = average_gain.div(average_loss.replace(0, np.nan))
    result["rsi"] = 100.0 - 100.0 / (1.0 + relative_strength)
    result.loc[(average_loss == 0) & (average_gain > 0), "rsi"] = 100.0

    result["bollinger_mid"] = grouped.transform(
        lambda values: values.rolling(band_window, min_periods=band_window).mean()
    )
    band_std = grouped.transform(
        lambda values: values.rolling(band_window, min_periods=band_window).std(ddof=0)
    )
    result["bollinger_upper"] = result["bollinger_mid"] + 2.0 * band_std
    result["bollinger_lower"] = result["bollinger_mid"] - 2.0 * band_std
    return result
