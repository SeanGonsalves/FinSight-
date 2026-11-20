"""Static, reproducible figures for reports and notebooks."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from finsight.metrics import daily_returns, rolling_volatility

sns.set_theme(style="whitegrid", context="notebook")


def _save(figure: plt.Figure, output_path: Path | str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return path


def _period_label(frame: pd.DataFrame) -> str:
    dates = pd.to_datetime(frame["date"])
    return f"{dates.min().date()} to {dates.max().date()}"


def plot_normalized_prices(
    frame: pd.DataFrame,
    symbols: Iterable[str],
    output_path: Path | str,
) -> Path:
    selected = frame.loc[frame["symbol"].isin(symbols)]
    wide = selected.pivot(index="date", columns="symbol", values="close").sort_index()
    normalized = wide.divide(wide.apply(lambda column: column.dropna().iloc[0])).mul(100)
    figure, axis = plt.subplots(figsize=(12, 6))
    normalized.plot(ax=axis, linewidth=1.2)
    axis.set(
        title=(
            "Normalized closing prices (first observed close = 100)\n"
            f"Source close; adjustment status unknown; {_period_label(selected)}"
        ),
        xlabel="Date",
        ylabel="Index",
    )
    axis.legend(title="Symbol", ncol=2)
    return _save(figure, output_path)


def plot_return_distributions(
    frame: pd.DataFrame,
    symbols: Iterable[str],
    output_path: Path | str,
) -> Path:
    selected = daily_returns(frame.loc[frame["symbol"].isin(symbols)]).dropna(
        subset=["daily_return"]
    )
    figure, axis = plt.subplots(figsize=(11, 6))
    sns.boxplot(data=selected, x="symbol", y="daily_return", ax=axis, showfliers=False)
    axis.set(
        title=f"Daily return distributions ({_period_label(selected)})",
        xlabel="Symbol",
        ylabel="Daily simple return",
    )
    axis.tick_params(axis="x", rotation=35)
    return _save(figure, output_path)


def plot_price_distributions(
    frame: pd.DataFrame,
    symbols: Iterable[str],
    output_path: Path | str,
) -> Path:
    selected = frame.loc[frame["symbol"].isin(symbols)]
    symbols = sorted(selected["symbol"].unique())
    if not symbols:
        raise ValueError("No matching symbols for price distributions")
    rows = (len(symbols) + 4) // 5
    figure, axes = plt.subplots(rows, 5, figsize=(14, 3.5 * rows), squeeze=False)
    for axis, symbol in zip(axes.flat, symbols):
        sns.histplot(
            selected.loc[selected["symbol"].eq(symbol), "close"],
            bins=35,
            ax=axis,
            color="tab:blue",
        )
        axis.set(title=symbol, xlabel="Source close", ylabel="Sessions")
    for axis in axes.flat[len(symbols) :]:
        axis.set_visible(False)
    figure.suptitle(f"Daily closing-price distributions ({_period_label(selected)})")
    return _save(figure, output_path)


def plot_volume(
    frame: pd.DataFrame,
    symbols: Iterable[str],
    output_path: Path | str,
) -> Path:
    selected = frame.loc[frame["symbol"].isin(symbols)]
    if "volume" not in selected:
        raise ValueError("volume column is required")
    daily = selected.pivot(index="date", columns="symbol", values="volume").sort_index()
    figure, axis = plt.subplots(figsize=(12, 6))
    for symbol in daily.columns:
        axis.plot(daily.index, daily[symbol], label=symbol, linewidth=0.8, alpha=0.8)
    axis.set_yscale("log")
    axis.set(
        title=f"Daily traded volume (log scale; {_period_label(selected)})",
        xlabel="Date",
        ylabel="Volume (source units)",
    )
    axis.legend(title="Symbol", ncol=2)
    return _save(figure, output_path)


def plot_monthly_returns(monthly: pd.DataFrame, output_path: Path | str) -> Path:
    required = {"period", "symbol", "return"}
    if not required.issubset(monthly.columns):
        raise ValueError(f"Required columns: {sorted(required)}")
    data = monthly.dropna(subset=["return"]).copy()
    data["date"] = data["period"].dt.to_timestamp()
    figure, axis = plt.subplots(figsize=(12, 6))
    for symbol, group in data.groupby("symbol", sort=True):
        axis.plot(group["date"], group["return"], label=symbol, linewidth=0.9)
    axis.set(title="Monthly close-to-close returns", xlabel="Month", ylabel="Simple return")
    axis.legend(title="Symbol", ncol=2)
    return _save(figure, output_path)


def plot_rolling_volatility(
    frame: pd.DataFrame,
    symbols: Iterable[str],
    output_path: Path | str,
    *,
    window: int = 20,
) -> Path:
    data = rolling_volatility(frame.loc[frame["symbol"].isin(symbols)], window=window)
    figure, axis = plt.subplots(figsize=(12, 6))
    for symbol, group in data.groupby("symbol", sort=True):
        axis.plot(group["date"], group["rolling_volatility"], label=symbol, linewidth=1)
    axis.set(
        title=f"{window}-session rolling annualized volatility ({_period_label(data)})",
        xlabel="Date",
        ylabel="Annualized volatility",
    )
    axis.legend(title="Symbol", ncol=2)
    return _save(figure, output_path)


def plot_drawdown(
    frame: pd.DataFrame,
    symbols: Iterable[str],
    output_path: Path | str,
) -> Path:
    selected = daily_returns(frame.loc[frame["symbol"].isin(symbols)]).dropna(
        subset=["daily_return"]
    )
    figure, axis = plt.subplots(figsize=(12, 6))
    for symbol, group in selected.groupby("symbol", sort=True):
        wealth = (1.0 + group["daily_return"]).cumprod()
        drawdown = wealth.div(wealth.cummax()).sub(1.0)
        axis.plot(group["date"], drawdown, label=symbol, linewidth=0.9)
    axis.set(
        title=f"Drawdown from prior wealth peak ({_period_label(selected)})",
        xlabel="Date",
        ylabel="Drawdown",
    )
    axis.legend(title="Symbol", ncol=2)
    return _save(figure, output_path)


def plot_correlation_heatmap(
    correlation: pd.DataFrame,
    output_path: Path | str,
    *,
    title: str = "Daily return correlation",
) -> Path:
    figure, axis = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        correlation,
        cmap="vlag",
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        ax=axis,
    )
    axis.set_title(title)
    return _save(figure, output_path)


def plot_rolling_correlation(
    correlations: pd.DataFrame,
    first_symbol: str,
    second_symbol: str,
    output_path: Path | str,
    *,
    window: int = 60,
) -> Path:
    if not {"date", "rolling_correlation"}.issubset(correlations.columns):
        raise ValueError("date and rolling_correlation columns are required")
    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(correlations["date"], correlations["rolling_correlation"], linewidth=0.9)
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(
        title=f"{window}-session rolling return correlation: {first_symbol} vs {second_symbol}",
        xlabel="Date",
        ylabel="Pearson correlation",
        ylim=(-1, 1),
    )
    return _save(figure, output_path)


def plot_annual_returns(annual: pd.DataFrame, output_path: Path | str) -> Path:
    required = {"symbol", "year", "annual_return"}
    if not required.issubset(annual.columns):
        raise ValueError(f"Required columns: {sorted(required)}")
    pivot = annual.pivot(index="year", columns="symbol", values="annual_return")
    figure, axis = plt.subplots(figsize=(12, 6))
    sns.heatmap(pivot, cmap="vlag", center=0, ax=axis, cbar_kws={"label": "Annual return"})
    axis.set(title="Calendar-year simple returns", xlabel="Symbol", ylabel="Calendar year")
    return _save(figure, output_path)


def plot_technical_indicators(frame: pd.DataFrame, symbol: str, output_path: Path | str) -> Path:
    data = frame.loc[frame["symbol"].eq(symbol)].sort_values("date")
    if data.empty:
        raise ValueError(f"No rows found for {symbol}")
    figure, (price_axis, rsi_axis) = plt.subplots(
        2, 1, figsize=(13, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    price_axis.plot(data["date"], data["close"], label="Close", linewidth=1)
    for column in ["sma_20", "sma_50", "bollinger_upper", "bollinger_lower"]:
        if column in data:
            price_axis.plot(data["date"], data[column], label=column.replace("_", " "), linewidth=0.8)
    price_axis.set(
        title=f"{symbol}: price and descriptive indicators ({_period_label(data)})",
        ylabel="Price (source local currency)",
    )
    price_axis.legend(ncol=3)
    if "rsi" in data:
        rsi_axis.plot(data["date"], data["rsi"], color="tab:purple", linewidth=0.9)
        rsi_axis.axhline(70, linestyle="--", color="gray", linewidth=0.8)
        rsi_axis.axhline(30, linestyle="--", color="gray", linewidth=0.8)
    rsi_axis.set(xlabel="Date", ylabel="RSI")
    return _save(figure, output_path)


def plot_predictions(
    predictions: pd.DataFrame,
    model: str,
    output_path: Path | str,
) -> Path:
    data = predictions.loc[predictions["model"].eq(model)].sort_values("date")
    if data.empty:
        raise ValueError(f"No predictions found for {model}")
    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(data["date"], data["actual_return"], label="Actual", linewidth=1)
    axis.plot(data["date"], data["predicted_return"], label="Predicted", linewidth=1)
    axis.set(
        title=f"Chronological test: next-session returns ({model}; {_period_label(data)})",
        xlabel="Target date",
        ylabel="Return",
    )
    axis.legend()
    return _save(figure, output_path)


def plot_residuals(
    predictions: pd.DataFrame,
    model: str,
    output_path: Path | str,
) -> Path:
    data = predictions.loc[predictions["model"].eq(model)].sort_values("date").copy()
    if data.empty:
        raise ValueError(f"No predictions found for {model}")
    residual = data["actual_return"] - data["predicted_return"]
    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].scatter(data["predicted_return"], residual, s=12, alpha=0.6)
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set(xlabel="Predicted return", ylabel="Residual", title="Residuals vs prediction")
    axes[1].hist(residual, bins=30, color="tab:blue", alpha=0.8)
    axes[1].set(xlabel="Residual", ylabel="Count", title="Residual distribution")
    figure.suptitle(f"{model} held-out residuals ({_period_label(data)})")
    return _save(figure, output_path)
