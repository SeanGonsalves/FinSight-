"""Currency-aware comparisons using Yahoo adjusted-close observations."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


def load_adjusted_comparison_data(
    india_dir: Path | str,
    usa_dir: Path | str,
    fx_path: Path | str,
) -> pd.DataFrame:
    """Load selected India/US adjusted closes and prior-observation USD/INR."""
    india_paths = sorted(Path(india_dir).glob("india_yahoo_*.parquet"))
    usa_paths = sorted(Path(usa_dir).glob("usa_*.parquet"))
    if not india_paths:
        raise FileNotFoundError(f"No adjusted Indian Yahoo files in {india_dir}")
    if not usa_paths:
        raise FileNotFoundError(f"No US Yahoo files in {usa_dir}")
    if not Path(fx_path).is_file():
        raise FileNotFoundError(f"USD/INR file not found: {fx_path}")

    frames: list[pd.DataFrame] = []
    for path, market, currency in [
        *((path, "INDIA", "INR") for path in india_paths),
        *((path, "USA", "USD") for path in usa_paths),
    ]:
        frame = pd.read_parquet(path)
        required = {"date", "symbol", "adj_close"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path.name}: missing fields {sorted(missing)}")
        frame = frame[["date", "symbol", "adj_close"]].copy()
        frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
        frame["adj_close"] = pd.to_numeric(frame["adj_close"], errors="raise")
        frame["market"] = market
        frame["currency"] = currency
        if frame["date"].duplicated().any():
            raise ValueError(f"{path.name}: duplicate dates")
        if frame["adj_close"].isna().any() or (frame["adj_close"] <= 0).any():
            raise ValueError(f"{path.name}: missing or nonpositive adjusted close")
        frames.append(frame)

    prices = pd.concat(frames, ignore_index=True)
    if prices.duplicated(["market", "symbol", "date"]).any():
        raise ValueError("Duplicate market/symbol/date rows in comparison inputs")
    fx = pd.read_parquet(fx_path, columns=["date", "close"])
    fx["date"] = pd.to_datetime(fx["date"], errors="raise").dt.normalize()
    fx = fx.rename(columns={"date": "fx_date", "close": "inr_per_usd"})
    fx = fx.sort_values("fx_date")
    if fx["fx_date"].duplicated().any():
        raise ValueError("USD/INR data contains duplicate dates")
    if fx["inr_per_usd"].isna().any() or (fx["inr_per_usd"] <= 0).any():
        raise ValueError("USD/INR data contains missing or nonpositive rates")

    india = prices.loc[prices["market"].eq("INDIA")].sort_values("date")
    if not india.empty:
        india = pd.merge_asof(
            india,
            fx,
            left_on="date",
            right_on="fx_date",
            direction="backward",
            allow_exact_matches=False,
            tolerance=pd.Timedelta(days=7),
        )
        india["adj_close_usd"] = india["adj_close"] / india["inr_per_usd"]
        before_first_rate = india["date"].le(fx["fx_date"].min())
        if (india["inr_per_usd"].isna() & ~before_first_rate).any():
            raise ValueError(
                "USD/INR data has missing coverage after its first available date"
            )
    usa = prices.loc[prices["market"].eq("USA")].copy()
    usa["inr_per_usd"] = np.nan
    usa["fx_date"] = pd.NaT
    usa["adj_close_usd"] = usa["adj_close"]
    result = pd.concat([india, usa], ignore_index=True)
    return result.sort_values(["market", "symbol", "date"], ignore_index=True)


def _performance_metrics(prices: pd.Series, returns: pd.Series) -> dict[str, float | int]:
    prices = prices.dropna()
    returns = returns.dropna()
    if prices.empty or returns.empty:
        raise ValueError("At least two valid prices are required for performance metrics")
    total_return = float(prices.iloc[-1] / prices.iloc[0] - 1.0)
    elapsed_days = (prices.index[-1] - prices.index[0]).days
    annualized_return = (
        float((prices.iloc[-1] / prices.iloc[0]) ** (365.25 / elapsed_days) - 1.0)
        if elapsed_days > 0 and prices.iloc[-1] / prices.iloc[0] > 0
        else float("nan")
    )
    daily_volatility = float(returns.std(ddof=1))
    wealth = (1.0 + returns).cumprod()
    drawdown = wealth.div(wealth.cummax()).sub(1.0)
    return {
        "observations": int(len(returns)),
        "first_date": str(prices.index[0].date()),
        "last_date": str(prices.index[-1].date()),
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": daily_volatility * np.sqrt(252),
        "max_drawdown": float(drawdown.min()),
        "sharpe_zero_rf": (
            float(returns.mean() / daily_volatility * np.sqrt(252))
            if daily_volatility > 0
            else float("nan")
        ),
    }


def build_comparison_tables(
    prices: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return per-stock metrics, market medians, and equal-weight USD series."""
    required = {"date", "market", "symbol", "currency", "adj_close", "adj_close_usd"}
    missing = required.difference(prices.columns)
    if missing:
        raise ValueError(f"Missing comparison fields: {sorted(missing)}")

    metric_rows: list[dict[str, object]] = []
    daily_rows: list[pd.DataFrame] = []
    for (market, symbol, currency), group in prices.groupby(
        ["market", "symbol", "currency"], sort=True
    ):
        group = group.sort_values("date").set_index("date")
        local_returns = group["adj_close"].pct_change(fill_method=None)
        usd_returns = group["adj_close_usd"].pct_change(fill_method=None)
        basis_data = [
            ("local_currency", group["adj_close"], local_returns),
            ("USD", group["adj_close_usd"], usd_returns),
        ]
        for basis, price_series, return_series in basis_data:
            if basis == "USD" and market == "USA":
                continue
            valid_prices = price_series.dropna()
            valid_returns = return_series.dropna()
            if len(valid_prices) < 2:
                continue
            metric_rows.append(
                {
                    "market": market,
                    "symbol": symbol,
                    "currency_basis": basis,
                    "source_currency": currency,
                    **_performance_metrics(valid_prices, valid_returns),
                }
            )
        daily = pd.DataFrame(
            {
                "date": group.index,
                "market": market,
                "symbol": symbol,
                "local_return": local_returns.to_numpy(),
                "usd_return": usd_returns.to_numpy(),
            }
        )
        daily_rows.append(daily)

    per_stock = pd.DataFrame(metric_rows)
    if per_stock.empty:
        raise ValueError("No comparable return metrics were produced")
    market_summary = (
        per_stock.groupby(["market", "currency_basis"], as_index=False)
        .agg(
            stocks=("symbol", "nunique"),
            median_total_return=("total_return", "median"),
            median_annualized_return=("annualized_return", "median"),
            median_annualized_volatility=("annualized_volatility", "median"),
            median_max_drawdown=("max_drawdown", "median"),
            median_sharpe_zero_rf=("sharpe_zero_rf", "median"),
        )
        .sort_values(["currency_basis", "market"])
        .reset_index(drop=True)
    )

    daily = pd.concat(daily_rows, ignore_index=True)
    common_dates = set(daily.loc[daily["market"].eq("INDIA"), "date"]).intersection(
        daily.loc[daily["market"].eq("USA"), "date"]
    )
    daily = daily.loc[daily["date"].isin(common_dates)]
    market_daily = (
        daily.groupby(["market", "date"], as_index=False)[["local_return", "usd_return"]]
        .mean()
        .sort_values(["market", "date"])
    )
    market_daily["equal_weight_usd_wealth"] = market_daily.groupby("market")[
        "usd_return"
    ].transform(lambda values: (1.0 + values.fillna(0.0)).cumprod() * 100.0)
    return per_stock, market_summary, market_daily


def build_macro_correlations(
    market_daily: pd.DataFrame,
    macro_data: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Relate annual equal-weight local-currency returns to country CPI/GDP."""
    required_market = {"date", "market", "local_return"}
    required_macro = {"country_code", "year", "indicator_code", "value"}
    if not required_market.issubset(market_daily.columns):
        raise ValueError(f"Market data requires {sorted(required_market)}")
    if not required_macro.issubset(macro_data.columns):
        raise ValueError(f"Macro data requires {sorted(required_macro)}")

    annual = market_daily[["date", "market", "local_return"]].copy()
    annual["year"] = pd.to_datetime(annual["date"]).dt.year
    annual = (
        annual.groupby(["market", "year"])["local_return"]
        .apply(lambda returns: float((1.0 + returns.fillna(0.0)).prod() - 1.0))
        .rename("annual_equal_weight_return")
        .reset_index()
    )
    annual["country_code"] = annual["market"].map({"INDIA": "IND", "USA": "USA"})
    macro = macro_data.pivot_table(
        index=["country_code", "year"],
        columns="indicator_code",
        values="value",
        aggfunc="first",
    ).reset_index()
    merged = annual.merge(macro, on=["country_code", "year"], how="left")

    correlation_rows: list[dict[str, float | int | str]] = []
    for market, group in merged.groupby("market", sort=True):
        for indicator in ["FP.CPI.TOTL.ZG", "NY.GDP.MKTP.KD.ZG"]:
            if indicator not in group:
                continue
            paired = group[["annual_equal_weight_return", indicator]].dropna()
            if len(paired) < 3:
                continue
            pearson = stats.pearsonr(
                paired["annual_equal_weight_return"], paired[indicator]
            )
            spearman = stats.spearmanr(
                paired["annual_equal_weight_return"], paired[indicator]
            )
            correlation_rows.append(
                {
                    "market": market,
                    "country_code": str(group["country_code"].iloc[0]),
                    "indicator_code": indicator,
                    "observations": int(len(paired)),
                    "pearson_r": float(pearson.statistic),
                    "pearson_pvalue": float(pearson.pvalue),
                    "spearman_rho": float(spearman.statistic),
                    "spearman_pvalue": float(spearman.pvalue),
                }
            )
    return merged.sort_values(["market", "year"]).reset_index(drop=True), pd.DataFrame(
        correlation_rows
    )


def write_comparison_outputs(
    prices: pd.DataFrame,
    output_dir: Path | str,
    figures_dir: Path | str,
    report_path: Path | str,
    *,
    macro_data: pd.DataFrame | None = None,
) -> dict[str, Path]:
    """Write comparative metrics, figures, and a sourced, caveated report."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    output = Path(output_dir)
    figures = Path(figures_dir)
    output.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    per_stock, market_summary, market_daily = build_comparison_tables(prices)
    per_stock_path = output / "cross_market_stock_metrics.csv"
    summary_path = output / "cross_market_summary.csv"
    daily_path = output / "cross_market_equal_weight_usd.csv"
    per_stock.to_csv(per_stock_path, index=False)
    market_summary.to_csv(summary_path, index=False)
    market_daily.to_csv(daily_path, index=False)
    macro_paths: dict[str, Path] = {}
    if macro_data is not None:
        macro_annual, macro_correlations = build_macro_correlations(market_daily, macro_data)
        macro_annual_path = output / "annual_stock_macro_alignment.csv"
        macro_correlation_path = output / "stock_macro_correlations.csv"
        macro_annual.to_csv(macro_annual_path, index=False)
        macro_correlations.to_csv(macro_correlation_path, index=False)
        macro_paths = {
            "macro_annual_alignment": macro_annual_path,
            "macro_correlations": macro_correlation_path,
        }

    figure, axis = plt.subplots(figsize=(12, 6))
    for market, group in market_daily.groupby("market", sort=True):
        axis.plot(
            group["date"],
            group["equal_weight_usd_wealth"],
            label=market,
            linewidth=1.5,
        )
    axis.set(
        title="Equal-weight selected-stock portfolio (USD, adjusted close)\n"
        "Common observed dates; India uses prior-observation USD/INR",
        xlabel="Date",
        ylabel="Growth of 100 USD",
    )
    axis.legend(title="Selected universe")
    figure.tight_layout()
    figure.savefig(figures / "selected_universes_usd_growth.png", dpi=160, bbox_inches="tight")
    plt.close(figure)

    usd_summary = market_summary.loc[market_summary["currency_basis"].eq("USD")]
    figure, axis = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=usd_summary,
        x="market",
        y="median_annualized_volatility",
        hue="market",
        legend=False,
        ax=axis,
    )
    axis.set(
        title="Median selected-stock annualized volatility (USD-adjusted returns)",
        xlabel="Selected stock universe",
        ylabel="Median annualized volatility",
    )
    figure.tight_layout()
    figure.savefig(figures / "median_usd_volatility.png", dpi=160, bbox_inches="tight")
    plt.close(figure)

    macro_text = "No macroeconomic series was supplied in this run."
    if macro_data is not None:
        macro_annual, macro_correlations = build_macro_correlations(market_daily, macro_data)
        if not macro_correlations.empty:
            macro_lines = [
                f"- {row.market} vs {row.indicator_code}: n={row.observations}, "
                f"Pearson r={row.pearson_r:.3f} (p={row.pearson_pvalue:.3f}), "
                f"Spearman rho={row.spearman_rho:.3f} (p={row.spearman_pvalue:.3f})."
                for row in macro_correlations.itertuples(index=False)
            ]
            macro_text = (
                "Exploratory correlations of annual equal-weight local-currency returns "
                "with World Bank annual indicators:\n\n"
                + "\n".join(macro_lines)
                + "\n\nSample sizes are small; p-values are unadjusted and do not imply causation."
            )
        else:
            macro_text = (
                "Macro data were supplied, but no indicator/country pair had at least three "
                "complete annual observations; no correlations are reported."
            )
        figure, axes = plt.subplots(2, 2, figsize=(10, 8))
        macro_columns = ["FP.CPI.TOTL.ZG", "NY.GDP.MKTP.KD.ZG"]
        for row_index, market in enumerate(["INDIA", "USA"]):
            selection = macro_annual.loc[macro_annual["market"].eq(market)]
            for col_index, indicator in enumerate(macro_columns):
                axis = axes[row_index, col_index]
                if indicator in selection:
                    axis.scatter(
                        selection[indicator],
                        selection["annual_equal_weight_return"],
                        s=28,
                    )
                axis.set(
                    title=f"{market}: {indicator}",
                    xlabel="Annual macro indicator (%)",
                    ylabel="Annual local-currency stock return",
                )
        figure.tight_layout()
        figure.savefig(figures / "annual_stock_macro_relationships.png", dpi=160, bbox_inches="tight")
        plt.close(figure)

    india_rows = per_stock.loc[
        (per_stock["market"].eq("INDIA")) & (per_stock["currency_basis"].eq("USD"))
    ]
    usa_rows = per_stock.loc[
        (per_stock["market"].eq("USA")) & (per_stock["currency_basis"].eq("local_currency"))
    ]
    india_median = india_rows["annualized_return"].median()
    usa_median = usa_rows["annualized_return"].median()
    summary_lookup = market_summary.set_index(["market", "currency_basis"])
    india_vol = summary_lookup.loc[("INDIA", "USD"), "median_annualized_volatility"]
    usa_vol = summary_lookup.loc[("USA", "local_currency"), "median_annualized_volatility"]
    common_start = market_daily["date"].min().date()
    common_end = market_daily["date"].max().date()
    report = f"""# India–US Selected-Stock Comparison

## Data and scope

This comparison uses Yahoo Finance adjusted-close observations for nine Indian symbols (RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, SBIN, ITC, ONGC, WIPRO) and ten US symbols. `TATAMOTORS` is excluded because Yahoo Finance did not return its requested ticker; the replacement TMPV history is not assumed to be the same continuous security. Data cover the downloaded 2016–2025 interval. The Indian prices are auxiliary Yahoo histories, not the original NSE file series. The download client is [yfinance](https://github.com/ranaroussi/yfinance); review applicable Yahoo Finance terms before redistribution.

The adjusted close is used for both universes to account for provider-reported splits/dividends. This basis is provider-defined and is not independently verified. USD/INR is Yahoo Finance `USDINR=X`, interpreted as INR per USD. For each Indian market date, the most recent FX observation strictly before that date is used, avoiding use of a same-date FX close that may occur after the Indian equity close. The US adjusted close is already USD-denominated.

## Results

- Median per-stock annualized return in USD terms: India {india_median:.2%}; USA {usa_median:.2%}.
- Median per-stock annualized volatility in USD terms: India {india_vol:.2%}; USA {usa_vol:.2%}.
- Equal-weight daily portfolio paths use only dates on which both selected universes have observations; the shared-date period is {common_start} to {common_end}. Returns within each universe are the arithmetic mean across that universe's available selected stocks on a shared date.
- The [per-stock results](tables/cross_market_stock_metrics.csv), [selected-universe summary](tables/cross_market_summary.csv), and [shared-date daily series](tables/cross_market_equal_weight_usd.csv) contain detailed metrics. Annualized return uses elapsed calendar days; annualized volatility uses 252 sessions.

## Interpretation and limitations

These are comparisons of selected surviving tickers, not market indices. Stock selection is not capitalization weighted and does not address survivorship bias. Yahoo adjusted closes and FX history may be revised, and the India supplementary series differ from the original NSE files. The USD/INR alignment uses the previous available FX observation, not an official fixing. The local-currency and USD-basis metrics are both retained in the tables.

{macro_text}

Annual indicator inputs are from the [World Bank CPI series](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG) and [GDP growth series](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG); see the [macro data audit](../docs/MACRO_DATA_AUDIT.md). Method details are in the [project methodology](../docs/METHODOLOGY.md).

Results are descriptive, not causal, not financial advice, and not a forecast of future performance.
"""
    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report, encoding="utf-8")
    outputs = {
        "stock_metrics": per_stock_path,
        "market_summary": summary_path,
        "daily_series": daily_path,
        "report": report_file,
    }
    outputs.update(macro_paths)
    return outputs
