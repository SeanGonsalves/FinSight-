"""Return, performance, risk, and statistical metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

TRADING_DAYS_PER_YEAR = 252


def daily_returns(
    frame: pd.DataFrame,
    *,
    price_column: str = "close",
) -> pd.DataFrame:
    """Calculate close-to-close simple returns independently for each symbol."""
    required = {"date", "symbol", price_column}
    if not required.issubset(frame.columns):
        raise ValueError(f"Required columns: {sorted(required)}")
    result = frame.sort_values(["symbol", "date"]).copy()
    result["daily_return"] = result.groupby("symbol", sort=False)[price_column].pct_change(
        fill_method=None
    )
    return result


def periodic_returns(frame: pd.DataFrame, frequency: str) -> pd.DataFrame:
    """Compute month-end or year-end close returns by symbol."""
    if frequency not in {"M", "Y"}:
        raise ValueError("frequency must be 'M' or 'Y'")
    required = {"date", "symbol", "close"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Required columns: {sorted(required)}")
    data = frame.sort_values(["symbol", "date"]).copy()
    data["period"] = data["date"].dt.to_period(frequency)
    closes = (
        data.groupby(["symbol", "period"], as_index=False, sort=True)
        .tail(1)
        .sort_values(["symbol", "period"])
    )
    closes["return"] = closes.groupby("symbol", sort=False)["close"].pct_change(
        fill_method=None
    )
    return closes[["symbol", "period", "close", "return"]].reset_index(drop=True)


def _max_drawdown(returns: pd.Series) -> float:
    wealth = (1.0 + returns).cumprod()
    drawdown = wealth.div(wealth.cummax()).sub(1.0)
    return float(drawdown.min()) if not drawdown.empty else float("nan")


def risk_performance_summary(
    frame: pd.DataFrame,
    *,
    risk_free_rate: float = 0.0,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> pd.DataFrame:
    """Summarize annualized return/volatility, Sharpe, downside risk, and drawdown."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    data = daily_returns(frame).dropna(subset=["daily_return"])
    summaries: list[dict[str, float | int | str]] = []
    for symbol, group in data.groupby("symbol", sort=True):
        returns = group["daily_return"].astype(float)
        standard_deviation = returns.std(ddof=1)
        annualized_return = (1.0 + returns).prod() ** (periods_per_year / len(returns)) - 1.0
        annualized_volatility = standard_deviation * np.sqrt(periods_per_year)
        daily_rf = (1.0 + risk_free_rate) ** (1.0 / periods_per_year) - 1.0
        sharpe = (
            (returns.mean() - daily_rf) / standard_deviation * np.sqrt(periods_per_year)
            if standard_deviation > 0
            else float("nan")
        )
        downside_deviation = np.sqrt(np.square(np.minimum(returns, 0.0)).mean()) * np.sqrt(
            periods_per_year
        )
        summaries.append(
            {
                "symbol": str(symbol),
                "observations": int(len(returns)),
                "annualized_return": float(annualized_return),
                "annualized_volatility": float(annualized_volatility),
                "max_drawdown": _max_drawdown(returns),
                "sharpe_ratio": float(sharpe),
                "annualized_downside_deviation": float(downside_deviation),
            }
        )
    return pd.DataFrame(summaries)


def annual_returns(frame: pd.DataFrame) -> pd.DataFrame:
    """Calculate calendar-year close-to-close returns by symbol."""
    return periodic_returns(frame, "Y").rename(
        columns={"period": "year", "close": "year_end_close", "return": "annual_return"}
    )


def rolling_volatility(
    frame: pd.DataFrame,
    *,
    window: int = 20,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> pd.DataFrame:
    """Calculate rolling annualized sample volatility of daily returns."""
    if window < 2:
        raise ValueError("window must be at least 2")
    result = daily_returns(frame)
    result["rolling_volatility"] = result.groupby("symbol", sort=False)["daily_return"].transform(
        lambda values: values.rolling(window, min_periods=window).std(ddof=1)
        * np.sqrt(periods_per_year)
    )
    return result


def correlation_matrix(frame: pd.DataFrame, *, method: str = "pearson") -> pd.DataFrame:
    """Return a date-aligned correlation matrix of daily returns."""
    if method not in {"pearson", "spearman"}:
        raise ValueError("method must be 'pearson' or 'spearman'")
    returns = daily_returns(frame).pivot(index="date", columns="symbol", values="daily_return")
    return returns.corr(method=method, min_periods=30)


def correlation_significance(
    frame: pd.DataFrame,
    first_symbol: str,
    second_symbol: str,
) -> dict[str, float | int]:
    """Test Pearson and Spearman return correlations on overlapping dates."""
    returns = daily_returns(frame).pivot(index="date", columns="symbol", values="daily_return")
    if first_symbol not in returns or second_symbol not in returns:
        raise ValueError("Both symbols must be present in the input data")
    paired = returns[[first_symbol, second_symbol]].dropna()
    if len(paired) < 3:
        raise ValueError("At least three overlapping return observations are required")
    pearson = stats.pearsonr(paired[first_symbol], paired[second_symbol])
    spearman = stats.spearmanr(paired[first_symbol], paired[second_symbol])
    return {
        "observations": int(len(paired)),
        "pearson_r": float(pearson.statistic),
        "pearson_pvalue": float(pearson.pvalue),
        "spearman_rho": float(spearman.statistic),
        "spearman_pvalue": float(spearman.pvalue),
    }


def rolling_correlation(
    frame: pd.DataFrame,
    first_symbol: str,
    second_symbol: str,
    *,
    window: int = 60,
) -> pd.DataFrame:
    """Calculate rolling Pearson return correlation on shared observed dates."""
    if window < 2:
        raise ValueError("window must be at least 2")
    returns = daily_returns(frame).pivot(index="date", columns="symbol", values="daily_return")
    if first_symbol not in returns or second_symbol not in returns:
        raise ValueError("Both symbols must be present in the input data")
    paired = returns[[first_symbol, second_symbol]].dropna()
    correlation = paired[first_symbol].rolling(window, min_periods=window).corr(
        paired[second_symbol]
    )
    return correlation.rename("rolling_correlation").reset_index()


def adf_stationarity_test(values: pd.Series) -> dict[str, float | int]:
    """Run an Augmented Dickey-Fuller test on finite, nonconstant observations."""
    cleaned = pd.Series(values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna()
    if len(cleaned) < 20 or cleaned.nunique() < 2:
        raise ValueError("ADF test requires at least 20 finite, nonconstant observations")
    try:
        from statsmodels.tsa.stattools import adfuller
    except ImportError as exc:
        raise RuntimeError("Install statsmodels from requirements.txt to run the ADF test") from exc
    result = adfuller(cleaned.to_numpy(), autolag="AIC", result_object=True)
    return {
        "statistic": float(result.statistic),
        "pvalue": float(result.pvalue),
        "used_lag": int(result.lags),
        "observations": int(result.nobs),
        **{
            f"critical_value_{key}": float(value)
            for key, value in result.critical_values.items()
        },
    }
