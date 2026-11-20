"""Reproducible local analysis pipeline for available Indian daily data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from finsight.acquisition import INDIA_COMPARISON_TICKERS, US_TICKERS
from finsight.data import INDIAN_STOCKS, build_processed_india, load_processed_india
from finsight.indicators import add_technical_indicators
from finsight.metrics import (
    adf_stationarity_test,
    annual_returns,
    correlation_matrix,
    correlation_significance,
    daily_returns,
    periodic_returns,
    risk_performance_summary,
    rolling_correlation,
)
from finsight.modeling import evaluate_forecasts
from finsight.visualization import (
    plot_correlation_heatmap,
    plot_drawdown,
    plot_annual_returns,
    plot_normalized_prices,
    plot_predictions,
    plot_monthly_returns,
    plot_price_distributions,
    plot_residuals,
    plot_return_distributions,
    plot_rolling_correlation,
    plot_rolling_volatility,
    plot_technical_indicators,
    plot_volume,
)


def _write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def _percent(value: float) -> str:
    return f"{value:.2%}"


def _collect_market_coverage(raw_dir: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(raw_dir.glob("nse_*.parquet")):
        frame = pd.read_parquet(path, columns=["date", "symbol", "series"])
        frame["date"] = pd.to_datetime(frame["date"], errors="raise")
        rows.append(
            {
                "file": path.name,
                "rows": len(frame),
                "eq_rows": int(frame["series"].eq("EQ").sum()),
                "market_dates": int(frame["date"].nunique()),
                "symbols": int(frame["symbol"].nunique()),
                "first_date": frame["date"].min().date(),
                "last_date": frame["date"].max().date(),
            }
        )
    if not rows:
        raise FileNotFoundError(f"No annual NSE files found in {raw_dir}")
    return pd.DataFrame(rows)


def _write_reports(
    root: Path,
    coverage: pd.DataFrame,
    selected: pd.DataFrame,
    risk: pd.DataFrame,
    yearly: pd.DataFrame,
    monthly: pd.DataFrame,
    adf_results: pd.DataFrame,
    model_metrics: pd.DataFrame,
    selected_model: str,
    split_sizes: dict[str, int],
    residual_mean: float,
    residual_std: float,
) -> None:
    reports = root / "reports"
    date_min = selected["date"].min().date()
    date_max = selected["date"].max().date()
    symbols = sorted(selected["symbol"].unique())
    report_best = risk.sort_values("annualized_return", ascending=False).iloc[0]
    most_volatile = risk.sort_values("annualized_volatility", ascending=False).iloc[0]
    best_month = monthly.dropna(subset=["return"]).sort_values("return").iloc[-1]
    worst_month = monthly.dropna(subset=["return"]).sort_values("return").iloc[0]
    average_daily = daily_returns(selected).groupby("symbol")["daily_return"].mean()
    highest_average = average_daily.idxmax()
    baseline = model_metrics.loc[model_metrics["model"].eq("Zero-return baseline")].iloc[0]
    model_row = model_metrics.loc[model_metrics["model"].eq(selected_model)].iloc[0]
    test_winner = model_metrics.sort_values("mae").iloc[0]

    coverage.to_csv(reports / "tables" / "nse_yearly_coverage.csv", index=False)
    risk.to_csv(reports / "tables" / "risk_performance.csv", index=False)
    yearly.assign(year=yearly["year"].astype(str)).to_csv(
        reports / "tables" / "annual_returns.csv", index=False
    )
    adf_results.to_csv(reports / "tables" / "adf_tests.csv", index=False)
    model_metrics.to_csv(reports / "tables" / "model_comparison.csv", index=False)

    _write_markdown(
        reports / "exploratory_analysis_report.md",
        f"""
# Exploratory Analysis Report

## Scope and data

This report uses the annual India Parquet files, filtered to the `EQ` series and the requested Indian tickers. The processed dataset contains {int(pq.ParquetFile(root / "data" / "processed" / "india" / "eq_daily.parquet").metadata.num_rows):,} `EQ` rows across all symbols; this analysis uses {len(selected):,} selected-stock rows across {len(symbols)} symbols. The observed selected-stock date range is {date_min} to {date_max}.

## Observations

- Selected symbols: {", ".join(symbols)}.
- The source supplies daily OHLC, volume, turnover, and trade-count fields. This report does not infer a benchmark or market-wide return from security-level observations.
- [Annual-file coverage](tables/nse_yearly_coverage.csv) is listed in the result tables; price and volume charts are in `figures/eda/`.
- The source has no documented adjusted-close or corporate-action factor. Normalized prices and returns therefore inherit the annual files' undocumented price basis.

## Conclusion

The selected universe supports descriptive daily-stock analysis for the audited period. Resolve corporate-action treatment, listed-entity continuity, and security-level coverage before interpreting long-horizon comparisons as total returns. See the [dataset audit](dataset_audit_report.md) and [methodology](../docs/METHODOLOGY.md).
""",
    )

    _write_markdown(
        reports / "risk_performance_report.md",
        f"""
# Risk and Performance Report

## Measures

Daily simple returns use consecutive observed `EQ` closes. Annualized volatility and Sharpe use 252 sessions per year; the Sharpe calculation assumes a zero risk-free rate. Downside deviation is the annualized root-mean-square of negative daily returns. These assumptions are methodological choices, not source metadata.

## Findings

Across the selected stocks, {report_best['symbol']} has the highest annualized return ({_percent(report_best['annualized_return'])}) over its available period, while {most_volatile['symbol']} has the highest annualized volatility ({_percent(most_volatile['annualized_volatility'])}). Estimates are not corporate-action adjusted and should not be read as total-return or investment conclusions.

The highest observed monthly return is {best_month['symbol']} in {best_month['period']} ({_percent(best_month['return'])}); the lowest is {worst_month['symbol']} in {worst_month['period']} ({_percent(worst_month['return'])}). {highest_average} has the highest arithmetic average daily return in the selected sample ({_percent(float(average_daily.loc[highest_average]))}).

See the [risk table](tables/risk_performance.csv), [annual returns](tables/annual_returns.csv), [monthly returns](tables/monthly_returns.csv), and figures under `figures/performance/` and `figures/risk/`. Source adjustments and limitations are summarized in the [methodology](../docs/METHODOLOGY.md) and [limitations](../docs/LIMITATIONS.md).
""",
    )

    _write_markdown(
        reports / "ml_evaluation_report.md",
        f"""
# Predictive Model Evaluation

## Target and split

The models predict the next observed session's simple close-to-close return from lagged returns, trailing volatility/momentum, moving-average gaps, and (where available) volume change known at the observation date. Rows remain chronological; split sizes are train={split_sizes["train"]:,}, validation={split_sizes["validation"]:,}, and test={split_sizes["test"]:,}. Validation MAE selects a candidate. Candidates are then refit on train plus validation before the held-out test evaluation.

The validation-selected candidate was **{selected_model}**. Its test MAE is {model_row["mae"]:.6f}; the zero-return baseline test MAE is {baseline["mae"]:.6f}. The lowest test MAE in the comparison is **{test_winner["model"]}** ({test_winner["mae"]:.6f}). Test results are descriptive and must not be used to retroactively select a model.

For the validation-selected model, held-out residual mean is {residual_mean:.6f} and sample standard deviation is {residual_std:.6f}. Actual-versus-predicted and residual plots are saved under `figures/modelling/`.

## Metrics and limitations

MAE, MSE, RMSE, and R-squared are in the [model comparison table](tables/model_comparison.csv); validation scores are in [model validation](tables/model_validation.csv). MAPE is omitted because returns can be zero or arbitrarily close to zero, making percentage error unstable. A single historical split does not establish predictive skill. Price adjustments, regime changes, and transaction costs remain limitations; see [model evaluation notes](../docs/MODEL_EVALUATION.md).
""",
    )

    usa_dir = root / "data" / "raw" / "usa" / "stocks"
    india_adjusted_dir = root / "data" / "raw" / "india" / "yahoo_adjusted"
    india_adjusted_files = (
        list(india_adjusted_dir.glob("india_yahoo_*.parquet"))
        if india_adjusted_dir.exists()
        else []
    )
    fx_files = list((root / "data" / "raw").rglob("*usd*inr*")) + list(
        (root / "data" / "raw").rglob("*inr*usd*")
    )
    macro_dir = root / "data" / "raw" / "macroeconomic"
    macro_files = [
        path
        for path in macro_dir.iterdir()
        if path.is_file()
        and path.name != ".gitkeep"
        and not path.name.lower().startswith("usdinr")
    ] if macro_dir.exists() else []
    us_files = list(usa_dir.glob("*.parquet")) if usa_dir.exists() else []
    requested_us_tickers = set(US_TICKERS)
    downloaded_us_tickers = {
        path.stem.split("_")[1].upper()
        for path in us_files
        if len(path.stem.split("_")) > 2
    }
    downloaded_india_symbols = {
        path.stem.split("_")[2].upper()
        for path in india_adjusted_files
        if len(path.stem.split("_")) > 2
    }
    missing_comparison_inputs = []
    missing_india_symbols = set(INDIA_COMPARISON_TICKERS) - downloaded_india_symbols
    if missing_india_symbols:
        missing_comparison_inputs.append(
            "supplementary Indian adjusted-close files for "
            + ", ".join(sorted(missing_india_symbols))
        )
    missing_us_symbols = requested_us_tickers - downloaded_us_tickers
    if missing_us_symbols:
        missing_comparison_inputs.append(
            "US stock files for " + ", ".join(sorted(missing_us_symbols))
        )
    if not fx_files:
        missing_comparison_inputs.append("USD/INR rates")
    comparison_status = (
        "The comparison was not generated in this run because these optional input "
        f"categories are missing: {', '.join(missing_comparison_inputs)}."
        if missing_comparison_inputs
        else "The selected-stock comparison is generated from the supplementary Yahoo files."
    )
    macro_status = (
        "World Bank macro inputs were found; macro output is generated when the comparison runs."
        if macro_files
        else "No World Bank macro input was found; macro correlations are omitted."
    )
    _write_markdown(
        reports / "comparative_market_report.md",
        f"""
# India–US Selected-Stock Comparison

## Input availability

| Input | Files found |
|---|---:|
| Supplementary Indian adjusted-close histories | {len(india_adjusted_files)} |
| US stock histories | {len(us_files)} ({len(downloaded_us_tickers)} of 10 requested tickers) |
| USD/INR histories | {len(fx_files)} |
| Non-FX macroeconomic files | {len(macro_files)} |

{comparison_status}

{macro_status}

The original annual India prices are not replaced or combined with the supplementary Yahoo histories. The separate mixed-cadence shard remains excluded. See the [US data audit](../docs/US_DATA_AUDIT.md), [data-source register](../docs/DATA_SOURCES.md), and [methodology](../docs/METHODOLOGY.md).
""",
    )

    top_year = yearly.dropna(subset=["annual_return"]).sort_values("annual_return").iloc[-1]
    adf_line = (
        f"The ADF p-value for {adf_results.iloc[0]['series']} is "
        f"{adf_results.iloc[0]['pvalue']:.6g}."
        if not adf_results.empty
        else "ADF results were not produced."
    )
    _write_markdown(
        reports / "comprehensive_project_report.md",
        f"""
# FinSight: Comprehensive Project Report

## Research scope

FinSight examines daily Indian stock prices for the requested symbols over {date_min}–{date_max}. Primary India results use the annual India Parquet files. Optional selected-stock comparisons use separate Yahoo adjusted-close and USD/INR files when present; macro correlations also require the World Bank annual input. This run found {len(india_adjusted_files)} supplementary Indian price file(s), {len(us_files)} US stock file(s), {len(fx_files)} candidate FX file(s), and {len(macro_files)} non-FX macro file(s).

## Data and method

The annual files provide daily OHLCV-style fields. The analysis filters `series == EQ`, checks required values and OHLC relationships, computes daily/monthly/yearly simple returns, uses a 252-session annualization convention, evaluates Pearson/Spearman return correlations, calculates descriptive technical indicators, and evaluates next-session returns using chronological train/validation/test data. The separate `train-00000.parquet` shard is excluded because of mixed cadence, data anomalies, unverified provenance, and price conflicts with the annual files.

## Findings from this run

- The best selected-stock annualized return is {report_best['symbol']} ({_percent(report_best['annualized_return'])}); the highest annualized volatility is {most_volatile['symbol']} ({_percent(most_volatile['annualized_volatility'])}).
- The strongest single calendar-year selected-stock return in the available annual table is {top_year['symbol']} in {top_year['year']} ({_percent(top_year['annual_return'])}).
- {adf_line} ADF interpretation is conditional on the test specification and does not establish economic causation.
- Validation selected {selected_model}; its test MAE ({model_row['mae']:.6f}) is compared with the zero-return baseline ({baseline['mae']:.6f}). This is one chronological evaluation, not evidence of deployable predictive performance.
- Cross-market and macro results are in the [comparative report](comparative_market_report.md) when their optional inputs are available.

## Interpretation and limitations

These are descriptive estimates from the available source series. Adjustment status is undocumented; splits, dividends, survivorship, company/ticker transitions, differing trading calendars, and omitted delisted securities can affect results. Correlation is not causation. Forecasts are not financial advice or guaranteed outcomes.

Generated tables are under `tables/`; figures are under `figures/`. Re-run `python scripts/run_analysis.py` to regenerate the primary outputs. See [methodology](../docs/METHODOLOGY.md), [data sources](../docs/DATA_SOURCES.md), and [limitations](../docs/LIMITATIONS.md) for interpretation details.
""",
    )


def run_analysis(
    root: Path | str,
    *,
    forecast_symbol: str = "RELIANCE",
    overwrite_processed: bool = False,
) -> dict[str, Path]:
    """Build the processed Indian dataset and generate local analysis outputs."""
    project_root = Path(root).resolve()
    raw_dir = project_root / "data" / "raw" / "india" / "stocks"
    processed_path = project_root / "data" / "processed" / "india" / "eq_daily.parquet"
    if not processed_path.exists() or overwrite_processed:
        build_processed_india(raw_dir, processed_path, overwrite=overwrite_processed)

    coverage = _collect_market_coverage(raw_dir)
    selected = load_processed_india(processed_path, symbols=INDIAN_STOCKS)
    selected = selected.loc[
        selected["date"].between("2016-01-01", "2025-12-31")
    ].copy()
    if forecast_symbol not in set(selected["symbol"]):
        raise ValueError(f"{forecast_symbol} is not available in the selected Indian data")

    reports = project_root / "reports"
    figures = reports / "figures"
    tables = reports / "tables"
    for folder in [
        figures / "eda",
        figures / "performance",
        figures / "risk",
        figures / "correlation",
        figures / "technical",
        figures / "modelling",
        tables,
    ]:
        folder.mkdir(parents=True, exist_ok=True)

    symbols = sorted(selected["symbol"].unique())
    risk = risk_performance_summary(selected)
    yearly = annual_returns(selected)
    monthly = periodic_returns(selected, "M")
    correlations = correlation_matrix(selected, method="pearson")
    spearman = correlation_matrix(selected, method="spearman")
    pair_test = correlation_significance(selected, symbols[0], symbols[1])
    rolling_corr = rolling_correlation(selected, "RELIANCE", "TCS", window=60)

    _write_markdown(
        reports / "tables" / "correlation_test.md",
        f"""
# Pairwise Return-Correlation Test

Pearson and Spearman tests use the overlapping daily returns for {symbols[0]} and {symbols[1]}.
The annual India source price adjustment is undocumented; p-values do not establish causation.

| Statistic | Result |
|---|---:|
| Paired observations | {pair_test["observations"]:,} |
| Pearson r | {pair_test["pearson_r"]:.6f} |
| Pearson two-sided p-value | {pair_test["pearson_pvalue"]:.6g} |
| Spearman rho | {pair_test["spearman_rho"]:.6f} |
| Spearman two-sided p-value | {pair_test["spearman_pvalue"]:.6g} |

See the [methodology](../../docs/METHODOLOGY.md) and [limitations](../../docs/LIMITATIONS.md).
""",
    )
    correlations.to_csv(tables / "pearson_return_correlations.csv")
    spearman.to_csv(tables / "spearman_return_correlations.csv")
    rolling_corr.to_csv(tables / "reliance_tcs_rolling_correlation.csv", index=False)
    monthly.assign(period=monthly["period"].astype(str)).to_csv(
        tables / "monthly_returns.csv", index=False
    )
    combined_dir = project_root / "data" / "processed" / "combined"
    combined_dir.mkdir(parents=True, exist_ok=True)
    daily_returns(selected).to_parquet(
        combined_dir / "india_selected_daily_returns.parquet", index=False
    )

    selected_symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "ONGC", "WIPRO", "TATAMOTORS"]
    plot_normalized_prices(
        selected,
        selected_symbols,
        figures / "performance" / "normalized_closes.png",
    )
    plot_annual_returns(yearly, figures / "performance" / "annual_returns.png")
    plot_return_distributions(
        selected,
        selected_symbols,
        figures / "eda" / "daily_return_distributions.png",
    )
    plot_price_distributions(
        selected,
        selected_symbols,
        figures / "eda" / "closing_price_distributions.png",
    )
    plot_volume(selected, selected_symbols, figures / "eda" / "trading_volume.png")
    plot_rolling_volatility(
        selected,
        selected_symbols,
        figures / "risk" / "rolling_volatility.png",
    )
    plot_drawdown(selected, selected_symbols, figures / "risk" / "drawdowns.png")
    plot_correlation_heatmap(correlations, figures / "correlation" / "pearson_heatmap.png")
    plot_correlation_heatmap(
        spearman,
        figures / "correlation" / "spearman_heatmap.png",
        title="Spearman daily return correlation",
    )
    plot_rolling_correlation(
        rolling_corr,
        "RELIANCE",
        "TCS",
        figures / "correlation" / "reliance_tcs_rolling_correlation.png",
    )
    plot_monthly_returns(monthly, figures / "performance" / "monthly_returns.png")

    indicator_data = add_technical_indicators(
        selected.loc[selected["symbol"].eq(forecast_symbol)]
    )
    indicator_data.to_parquet(
        combined_dir / f"{forecast_symbol.lower()}_indicators.parquet",
        index=False,
    )
    plot_technical_indicators(
        indicator_data,
        forecast_symbol,
        figures / "technical" / f"{forecast_symbol.lower()}_indicators.png",
    )

    adf_rows = []
    stock_data = selected.loc[selected["symbol"].eq(forecast_symbol)].sort_values("date")
    stock_returns = stock_data["close"].pct_change(fill_method=None)
    for series_name, values in [("close", stock_data["close"]), ("daily_return", stock_returns)]:
        adf_rows.append({"symbol": forecast_symbol, "series": series_name, **adf_stationarity_test(values)})
    adf_results = pd.DataFrame(adf_rows)

    forecast = evaluate_forecasts(stock_data)
    forecast.metrics.to_csv(tables / "model_comparison.csv", index=False)
    forecast.validation_metrics.to_csv(tables / "model_validation.csv", index=False)
    forecast.predictions.to_parquet(
        combined_dir / "forecast_predictions.parquet",
        index=False,
    )
    plot_predictions(
        forecast.predictions,
        forecast.selected_model,
        figures / "modelling" / f"{forecast_symbol.lower()}_test_predictions.png",
    )
    selected_predictions = forecast.predictions.loc[
        forecast.predictions["model"].eq(forecast.selected_model)
    ]
    residuals = selected_predictions["actual_return"] - selected_predictions["predicted_return"]
    plot_residuals(
        forecast.predictions,
        forecast.selected_model,
        figures / "modelling" / f"{forecast_symbol.lower()}_residuals.png",
    )

    _write_reports(
        project_root,
        coverage,
        selected,
        risk,
        yearly,
        monthly,
        adf_results,
        forecast.metrics,
        forecast.selected_model,
        forecast.split_sizes,
        float(residuals.mean()),
        float(residuals.std(ddof=1)),
    )
    outputs = {
        "processed_data": processed_path,
        "risk_table": tables / "risk_performance.csv",
        "model_table": tables / "model_comparison.csv",
        "comprehensive_report": reports / "comprehensive_project_report.md",
    }
    india_adjusted_dir = raw_dir.parent / "yahoo_adjusted"
    usa_dir = project_root / "data" / "raw" / "usa" / "stocks"
    fx_path = project_root / "data" / "raw" / "macroeconomic" / "usdinr_yahoo_2016_2025.parquet"
    macro_path = project_root / "data" / "raw" / "macroeconomic" / "world_bank_annual_2016_2025.parquet"
    india_adjusted_files = list(india_adjusted_dir.glob("india_yahoo_*.parquet"))
    usa_files = list(usa_dir.glob("usa_*.parquet"))
    required_india_symbols = set(INDIA_COMPARISON_TICKERS)
    available_india_symbols = {
        path.stem.split("_")[2].upper()
        for path in india_adjusted_files
        if len(path.stem.split("_")) > 2
    }
    available_us_symbols = {
        path.stem.split("_")[1].upper()
        for path in usa_files
        if len(path.stem.split("_")) > 2
    }
    if (
        required_india_symbols.issubset(available_india_symbols)
        and set(US_TICKERS).issubset(available_us_symbols)
        and fx_path.is_file()
    ):
        from finsight.comparison import load_adjusted_comparison_data, write_comparison_outputs

        comparison_prices = load_adjusted_comparison_data(india_adjusted_dir, usa_dir, fx_path)
        outputs.update(
            write_comparison_outputs(
                comparison_prices,
                tables,
                figures / "performance",
                reports / "comparative_market_report.md",
                macro_data=pd.read_parquet(macro_path) if macro_path.exists() else None,
            )
        )
        comparison_summary = pd.read_csv(tables / "cross_market_summary.csv")
        india_usd = comparison_summary.loc[
            (comparison_summary["market"] == "INDIA")
            & (comparison_summary["currency_basis"] == "USD")
        ].iloc[0]
        usa_local = comparison_summary.loc[
            (comparison_summary["market"] == "USA")
            & (comparison_summary["currency_basis"] == "local_currency")
        ].iloc[0]
        macro_summary_path = tables / "stock_macro_correlations.csv"
        macro_summary = (
            pd.read_csv(macro_summary_path)
            if macro_path.is_file() and macro_summary_path.exists()
            else pd.DataFrame()
        )
        macro_text = (
            "; ".join(
                f"{row.market}/{row.indicator_code}: Pearson r={row.pearson_r:.3f}, "
                f"n={row.observations}"
                for row in macro_summary.itertuples(index=False)
            )
            if not macro_summary.empty
            else "no macroeconomic series were available"
        )
        comprehensive_path = reports / "comprehensive_project_report.md"
        with comprehensive_path.open("a", encoding="utf-8") as report_file:
            report_file.write(
                "\n## Selected-stock cross-market comparison\n\n"
                f"The median per-stock annualized adjusted-close return was "
                f"{india_usd['median_annualized_return']:.2%} for the Indian selected universe "
                f"in USD and {usa_local['median_annualized_return']:.2%} for the US universe. "
                f"Median annualized volatilities were "
                f"{india_usd['median_annualized_volatility']:.2%} and "
                f"{usa_local['median_annualized_volatility']:.2%}, respectively. "
                "The detailed scope, FX convention, macro correlations, and caveats are in the "
                "[comparative report](comparative_market_report.md); this is not an index comparison. "
                f"Exploratory annual macro correlations: {macro_text}. The sample has only "
                "9–10 observations and does not establish causality.\n"
            )
    return outputs
