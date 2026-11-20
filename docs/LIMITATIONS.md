# Limitations and Interpretation

This note describes limits that affect the current FinSight analyses. It should be read alongside the [data-source register](DATA_SOURCES.md), [methodology](METHODOLOGY.md), and [dataset audit](../reports/dataset_audit_report.md).

## Data and coverage

- The original annual Parquet provider, retrieval history, and license are undocumented. File names alone do not prove an official exchange source.
- The annual India files do not document adjusted-close or corporate-action treatment. Their close-based results are not established total returns.
- The separate `train-00000.parquet` shard has unknown provenance, mixed midnight and intraday timestamps, data-quality anomalies, and price conflicts with annual files; it is excluded.
- The India–US comparison uses supplementary Yahoo adjusted closes for nine Indian and ten US symbols. It does not merge the supplementary Indian prices into the annual NSE files.
- Yahoo did not return the requested legacy `TATAMOTORS.NS` series. TMPV is not assumed to be a continuous equivalent, so Tata Motors is excluded from the comparison.
- Yahoo adjusted histories and FX values can change. Corporate-action fields returned by a provider are not independently validated.
- The annual-file coverage audit did not validate every observed date against an authoritative exchange holiday calendar. Delisted securities and survivorship effects are not comprehensively represented.
- Volume, turnover units/currency, and some source semantics are not documented. No comparable benchmark-index dataset is included.
- USD/INR uses `USDINR=X`, interpreted as INR per USD, with the most recent observation strictly before each Indian stock date. It is not an official fixing; the comparison also reflects market-calendar and timing differences.
- World Bank macro comparisons have only 9–10 paired annual observations. The 2025 US CPI value is missing and is not imputed.

## Statistical and model interpretation

- Correlation is not causation. The macro p-values are unadjusted, based on a very small sample, and do not address every multiple-testing or nonstationarity concern.
- ADF results depend on the tested series and lag-selection specification; rejection or non-rejection is not an economic conclusion.
- Technical indicators are descriptive transformations, not validated signals or trading rules.
- Risk annualization uses 252 sessions per year. The default Sharpe ratio uses a zero risk-free rate.
- The forecast experiment uses one chronological train/validation/test split and a fixed set of features and regressors. It does not simulate portfolio construction, execution, transaction costs, or slippage.
- A model's selection on validation data and performance on one historical test interval do not establish persistent or deployable forecasting skill.

## Scope and responsible use

FinSight provides local descriptive analysis and optional selected-stock / macro comparisons when the required supplementary files are available. The main pipeline skips the optional comparison when a required comparison input set is incomplete; the standalone comparison command reports missing required files. Missing observations are not synthesized.

Historical measurements and model outputs are for educational and research use. They are not investment, tax, or legal advice and do not guarantee future results.
