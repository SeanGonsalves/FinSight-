# Key Findings

This page distinguishes the initial local-data audit from later acquisitions and the current analysis outputs. It records observations from the documented pipeline run; refresh generated reports before citing exact metrics.

## Initial India-data audit

- Ten annual NSE-named Parquet files cover 2016–2025 and contain 4,597,797 rows in total.
- The annual files share a 16-column schema and include `EQ`, `BE`, and `BZ` series.
- All ten requested Indian tickers are observed in `EQ` records during the audited years. The legacy `TATAMOTORS` symbol ends on 2025-10-23; `TMPV` and `TMCV` appear later in 2025 and were not automatically joined.
- The audit found no null values in inspected fields, duplicate natural keys, nonpositive OHLC values, OHLC relationship violations, or nonpositive volume in the annual files.
- The separate 7,969,510-row shard has mixed midnight/intraday cadence, anomalies, unverified provenance, and price conflicts with annual files; it is excluded from analysis.
- At this initial audit stage, no US stock, USD/INR, or macroeconomic input was found. Subsequent acquisitions are recorded below.

Detailed schemas, checks, and later follow-ups are in the [dataset audit report](../reports/dataset_audit_report.md).

## US stock acquisition (2026-11-19)

- Yahoo Finance histories were retrieved for ten requested US tickers. Each file contains 2,514 records from 2016-01-04 to 2025-12-31, with raw OHLC, adjusted close, volume, and returned dividend/split fields.
- The audited files had no null cells, nonpositive OHLC values, OHLC relationship violations, or duplicate dates.
- This acquisition did not provide the supplementary Indian adjusted-price histories, USD/INR, or macro inputs; those were handled in the later comparison-data step.
- File-level counts and schema details are in the [US data audit](US_DATA_AUDIT.md).

## Comparison and macro inputs

- Separate Yahoo adjusted-close histories were acquired for nine Indian symbols. Tata Motors was omitted because Yahoo returned no legacy ticker history and TMPV was not treated as an interchangeable continuous series.
- Yahoo `USDINR=X` was acquired and aligned using the most recent rate strictly before each Indian equity date.
- World Bank annual CPI inflation and GDP growth series were acquired for India and the USA. The 2025 US CPI value is missing and is not imputed.
- The selected-stock comparison reports median per-stock annualized adjusted-close return in USD terms of 11.20% for the Indian selected universe and 21.35% for the US universe; median annualized volatility was 26.66% and 28.46%, respectively.
- Macro correlations use only 9–10 annual observations. None of the four reported Pearson tests has p < 0.05; this low-powered sample is not evidence that no relationship exists.
- Full assumptions and results are in the [comparative report](../reports/comparative_market_report.md) and [macro data audit](MACRO_DATA_AUDIT.md).

## India pipeline results

In the documented pipeline run:

- ICICIBANK had the highest annualized close-based return (18.04%); TATAMOTORS had the highest annualized volatility (43.34%).
- TATAMOTORS had the highest single calendar-year close-based return in the available annual table in 2021 (162.39%).
- The largest and smallest observed monthly close-based returns were TATAMOTORS in 2019-10 (51.30%) and RELIANCE in 2024-10 (-54.89%). These source-price discontinuities require corporate-action and adjustment verification before economic interpretation.
- ICICIBANK had the highest arithmetic average daily return in the selected sample (0.08%).
- For RELIANCE next-session returns, validation selected Linear Regression. Its test MAE was 0.010876 versus 0.010556 for the zero-return baseline; the baseline therefore had lower test MAE in that run.
- The ADF p-value for the RELIANCE close series was 0.382176 under the documented AIC lag selection.

These are source-close-based observations, not verified corporate-action-adjusted total returns. They do not imply predictive skill, causality, or future performance. Generated results and caveats are in the [exploratory](../reports/exploratory_analysis_report.md), [risk](../reports/risk_performance_report.md), [model evaluation](../reports/ml_evaluation_report.md), and [comprehensive](../reports/comprehensive_project_report.md) reports.
