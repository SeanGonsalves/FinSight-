# Project Information

## Project summary

**FinSight — Financial Market Intelligence & Comparative Stock Market Analysis**

FinSight is an academic Python data-science project for studying selected daily equity histories. It includes a local India-focused analysis pipeline and an optional selected-stock comparison with the United States when the required supplementary data are available.

## Objectives

- Inspect the available Parquet data and document source limitations.
- Validate and prepare annual Indian equity observations.
- Describe stock returns, risk, correlations, technical indicators, and stationarity tests.
- Evaluate a next-observed-session return example with chronological validation and a simple baseline.
- Compare selected Indian and US stocks in local and common currency using separate, documented adjusted-price histories.
- Relate annual equal-weight selected-stock returns to World Bank CPI and GDP growth as an exploratory analysis.

## Implemented scope and data

The primary local input is ten annual NSE-named Parquet files covering 2016–2025. The source provider and corporate-action treatment are undocumented, so the project does not assume these files are verified total-return histories or official exchange downloads. The `train-00000.parquet` shard remains excluded because provenance and price conventions are unresolved and its observations mix midnight and intraday timestamps.

Optional inputs in the current workspace include ten Yahoo Finance US ticker histories, Yahoo adjusted-close histories for nine Indian symbols, USD/INR, and World Bank annual CPI and GDP growth for India and the USA. These supplementary files are kept separate from the primary annual India files. The selected-stock comparison excludes Tata Motors because the requested legacy Yahoo ticker was unavailable and the replacement symbol was not assumed equivalent. See [data sources](DATA_SOURCES.md) and the [US](US_DATA_AUDIT.md) and [macro](MACRO_DATA_AUDIT.md) audits.

## Repository map

| Path | Purpose |
|---|---|
| `src/finsight/` | Data validation, acquisition, comparison, metrics, modelling, visualization, and pipeline functions |
| `scripts/` | Entry points for preparation, optional downloads, India analysis, and selected-stock comparison |
| `notebooks/` | Ten ordered audit and analysis notebooks |
| `tests/` | Focused regression tests for core calculations and data handling |
| `data/raw/` | Local source datasets, excluded from version control |
| `data/processed/` | Derived Parquet outputs |
| `reports/tables/` and `reports/figures/` | Generated result tables and charts |
| `reports/*.md` | Generated audit and analysis reports |
| `docs/` | Methodology, source provenance, findings, and limitations |

Use the [README](../README.md) for setup, execution order, and report links.

## Intended audience and use

The code and notebooks are intended for academic study and demonstration. Outputs are descriptive research artifacts, not recommendations, validated trading signals, or evidence of deployable forecasting skill.

## License

Project source code is provided under the repository's MIT license. Downloaded data remains subject to each source's terms and is not relicensed by this project.
