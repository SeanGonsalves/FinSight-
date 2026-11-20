# FinSight: Comprehensive Project Report

## Research scope

FinSight examines daily Indian stock prices for the requested symbols over 2016-01-01–2025-12-31. Primary India results use the annual India Parquet files. Optional selected-stock comparisons use separate Yahoo adjusted-close and USD/INR files when present; macro correlations also require the World Bank annual input. This run found 9 supplementary Indian price file(s), 10 US stock file(s), 1 candidate FX file(s), and 1 non-FX macro file(s).

## Data and method

The annual files provide daily OHLCV-style fields. The analysis filters `series == EQ`, checks required values and OHLC relationships, computes daily/monthly/yearly simple returns, uses a 252-session annualization convention, evaluates Pearson/Spearman return correlations, calculates descriptive technical indicators, and evaluates next-session returns using chronological train/validation/test data. The separate `train-00000.parquet` shard is excluded because of mixed cadence, data anomalies, unverified provenance, and price conflicts with the annual files.

## Findings from this run

- The best selected-stock annualized return is ICICIBANK (18.04%); the highest annualized volatility is TATAMOTORS (43.34%).
- The strongest single calendar-year selected-stock return in the available annual table is TATAMOTORS in 2021 (162.39%).
- The ADF p-value for close is 0.382176. ADF interpretation is conditional on the test specification and does not establish economic causation.
- Validation selected Linear Regression; its test MAE (0.010876) is compared with the zero-return baseline (0.010556). This is one chronological evaluation, not evidence of deployable predictive performance.
- Cross-market and macro results are in the [comparative report](comparative_market_report.md) when their optional inputs are available.

## Interpretation and limitations

These are descriptive estimates from the available source series. Adjustment status is undocumented; splits, dividends, survivorship, company/ticker transitions, differing trading calendars, and omitted delisted securities can affect results. Correlation is not causation. Forecasts are not financial advice or guaranteed outcomes.

Generated tables are under `tables/`; figures are under `figures/`. Re-run `python scripts/run_analysis.py` to regenerate the primary outputs. See [methodology](../docs/METHODOLOGY.md), [data sources](../docs/DATA_SOURCES.md), and [limitations](../docs/LIMITATIONS.md) for interpretation details.

## Selected-stock cross-market comparison

The median per-stock annualized adjusted-close return was 11.20% for the Indian selected universe in USD and 21.35% for the US universe. Median annualized volatilities were 26.66% and 28.46%, respectively. The detailed scope, FX convention, macro correlations, and caveats are in the [comparative report](comparative_market_report.md); this is not an index comparison. Exploratory annual macro correlations: INDIA/FP.CPI.TOTL.ZG: Pearson r=-0.021, n=10; INDIA/NY.GDP.MKTP.KD.ZG: Pearson r=-0.046, n=10; USA/FP.CPI.TOTL.ZG: Pearson r=-0.619, n=9; USA/NY.GDP.MKTP.KD.ZG: Pearson r=-0.143, n=10. The sample has only 9–10 observations and does not establish causality.
