# FinSight

**Financial market analysis of selected Indian and US equities**

FinSight is a reproducible Python research project for describing equity prices, returns, risk, correlations, technical indicators, and a carefully bounded next-session return modelling example. Its primary analysis uses annual India stock files; a separate, optional comparison uses supplementary Yahoo Finance adjusted-close histories and USD/INR. World Bank CPI inflation and GDP growth series support exploratory annual correlations.

FinSight is an academic analysis project, not a trading system or source of investment, tax, or legal advice. Results are not forecasts of future performance.

## What is included

- Validation and preparation of annual Indian equity Parquet files.
- Descriptive price, volume, return, risk, correlation, and stationarity analysis.
- Historical technical indicators computed from observed prices.
- Chronological next-session return evaluation against a zero-return baseline.
- An optional selected-stock India–US comparison using adjusted closes and prior-observation FX alignment.
- Exploratory alignment of annual selected-stock returns with World Bank CPI and GDP growth.
- Ten ordered notebooks, focused tests, figures, result tables, and generated reports.

The comparison is not an index comparison. The India and US universes are selected stocks, not capitalization-weighted market portfolios, and may be affected by survivorship bias.

## Data sources and status

| Input | Description and use | Provenance/status |
|---|---|---|
| Annual India Parquet files (`nse_2016.parquet`–`nse_2025.parquet`) | Daily OHLCV and related fields; the primary pipeline filters to `EQ` | Present in the audited workspace. The original provider, retrieval date, license, and adjustment basis are undocumented; do not attribute them to an official exchange feed. |
| `train-00000.parquet` | Separate shard inspected by the audit notebook | Present in the workspace but excluded from analysis because its source and price basis are unverified and its timestamps mix daily and intraday cadence. |
| Yahoo Finance US files | Ten US ticker histories, including adjusted close and returned corporate-action fields | Retrieved with [yfinance](https://github.com/ranaroussi/yfinance); source availability and terms can change. |
| Supplementary Yahoo Finance India histories | Adjusted-close histories for nine requested Indian stocks | Kept separate from the annual files. Tata Motors is excluded because the requested legacy symbol was not returned and TMPV was not assumed equivalent. |
| Yahoo Finance `USDINR=X` | INR-per-USD rate for the selected-stock comparison | Each Indian session is converted with the latest available rate strictly before its date. |
| World Bank annual indicators | CPI inflation and GDP growth for India and the USA | See the [CPI series](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG) and [GDP growth series](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG); the source API may revise historical values. |

The current workspace audit, source notes, and acquisition details are in [the dataset audit](reports/dataset_audit_report.md), [data-source register](docs/DATA_SOURCES.md), [US data audit](docs/US_DATA_AUDIT.md), and [macro data audit](docs/MACRO_DATA_AUDIT.md). Files under `data/raw/` and `data/processed/` are excluded from version control by `.gitignore`; a fresh checkout therefore needs the original files supplied locally and the optional data acquired separately.

## Analysis and methodology

The Indian pipeline retains the `EQ` series, validates required fields and OHLC relationships, computes close-to-close simple returns, and produces risk, correlation, technical-indicator, and chronological forecasting outputs. Annualization uses 252 sessions; Sharpe uses a zero risk-free rate unless changed in code. The forecasting example uses chronological train/validation/test splits and reports the zero-return baseline.

The supplementary comparison uses Yahoo adjusted closes for both selected universes rather than combining the differently sourced annual NSE prices with Yahoo prices. USD/INR conversion uses the previous available observation, not a same-day FX close or official fixing. The macro correlations have only 9–10 annual observations and are exploratory. Read [methodology](docs/METHODOLOGY.md), [limitations](docs/LIMITATIONS.md), and [model evaluation notes](docs/MODEL_EVALUATION.md) before interpreting results.

## Technology

- [Python](https://www.python.org/) and [Jupyter](https://jupyter.org/)
- [pandas](https://pandas.pydata.org/docs/), [NumPy](https://numpy.org/doc/stable/), [SciPy](https://docs.scipy.org/doc/scipy/), and [PyArrow](https://arrow.apache.org/docs/python/)
- [statsmodels](https://www.statsmodels.org/stable/), [scikit-learn](https://scikit-learn.org/stable/), [Matplotlib](https://matplotlib.org/stable/), and [Seaborn](https://seaborn.pydata.org/)
- [yfinance](https://github.com/ranaroussi/yfinance) for explicit optional Yahoo Finance downloads

Package versions are bounded in [requirements.txt](requirements.txt); project metadata is in [pyproject.toml](pyproject.toml).

## Project structure

```text
FinSight/
|-- .gitignore
|-- LICENSE
|-- README.md
|-- pyproject.toml
|-- requirements.txt
|-- data/
|   |-- external/                         Reserved for external inputs
|   |-- processed/
|   |   |-- combined/
|   |   |   |-- forecast_predictions.parquet
|   |   |   |-- india_selected_daily_returns.parquet
|   |   |   \-- reliance_indicators.parquet
|   |   |-- india/
|   |   |   \-- eq_daily.parquet
|   |   \-- usa/                          Placeholder; no processed US dataset
|   \-- raw/
|       |-- india/
|       |   |-- stocks/                   nse_2016.parquet ... nse_2025.parquet
|       |   |   \-- train-00000.parquet   Audited, excluded shard
|       |   \-- yahoo_adjusted/           Nine supplementary adjusted-price files
|       |-- macroeconomic/                USD/INR and World Bank annual data
|       \-- usa/stocks/                   Ten Yahoo Finance ticker files
|-- docs/
|   |-- DATA_DICTIONARY.md
|   |-- DATA_SOURCES.md
|   |-- KEY_FINDINGS.md
|   |-- LIMITATIONS.md
|   |-- MACRO_DATA_AUDIT.md
|   |-- METHODOLOGY.md
|   |-- MODEL_EVALUATION.md
|   |-- PROJECT_INFORMATION.md
|   \-- US_DATA_AUDIT.md
|-- notebooks/                            01_dataset_audit.ipynb ... 10_india_vs_us_analysis.ipynb
|-- reports/
|   |-- figures/                          Generated charts by analysis area
|   |-- tables/                           Generated CSV tables and correlation_test.md
|   |-- comparative_market_report.md
|   |-- comprehensive_project_report.md
|   |-- dataset_audit_report.md
|   |-- exploratory_analysis_report.md
|   |-- ml_evaluation_report.md
|   \-- risk_performance_report.md
|-- scripts/
|   |-- download_comparability_data.py
|   |-- download_macro_data.py
|   |-- download_us_data.py
|   |-- prepare_india_data.py
|   |-- run_analysis.py
|   \-- run_market_comparison.py
|-- src/finsight/
|   |-- __init__.py
|   |-- acquisition.py
|   |-- comparison.py
|   |-- data.py
|   |-- indicators.py
|   |-- metrics.py
|   |-- modeling.py
|   |-- pipeline.py
|   \-- visualization.py
\-- tests/
    \-- test_core.py
```

`data/raw/` and `data/processed/` are local data/output directories and are excluded from version control by the current `.gitignore`. Their files are present in this workspace; a fresh checkout may contain only the tracked placeholder files.

The local `src/finsight.egg-info/` directory is generated package metadata from the editable install, is ignored by `.gitignore`, and is intentionally omitted from the source tree above.

## Setup

From the project root in Windows PowerShell, create an environment and install the project dependencies:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

The package metadata declares Python 3.10 or later; the existing dependency bounds must also resolve for the interpreter you choose. The audited environment used Python 3.13.2. If the original India files are not present locally, place the ten annual files in `data/raw/india/stocks/` before running the India pipeline. Their acquisition instructions are not documented because their original provider is unknown.

## Run the analysis

### Prepare and validate the primary India data

```powershell
python scripts/prepare_india_data.py
```

This writes `data/processed/india/eq_daily.parquet` without changing the raw files. If the output already exists and should be rebuilt from the current inputs:

```powershell
python scripts/prepare_india_data.py --overwrite
```

### Generate India analysis outputs

```powershell
python scripts/run_analysis.py
```

The pipeline writes derived Parquet files under `data/processed/`, result tables under `reports/tables/`, figures under `reports/figures/`, and reports under `reports/`. To rebuild the processed India file as part of the run:

```powershell
python scripts/run_analysis.py --overwrite-processed
```

The forecasting example defaults to RELIANCE. A different available Indian symbol can be selected with:

```powershell
python scripts/run_analysis.py --symbol TCS
```

When supplementary adjusted-price and FX files are present, this run also rebuilds the cross-market and, if the macro file is present, annual macro outputs.

### Optional data acquisition and comparison

These commands make network requests. Review the data providers' terms and confirm that the downloads are appropriate for your use before running them:

```powershell
python scripts/download_us_data.py
python scripts/download_comparability_data.py
python scripts/download_macro_data.py
python scripts/run_market_comparison.py
```

The downloaders replace the corresponding named raw files. US and Indian histories come from Yahoo Finance through yfinance; annual CPI and GDP growth come from the World Bank Indicators API. The comparison script expects the downloaded US, Indian adjusted-close, and USD/INR files. The main pipeline also includes comparison outputs when those inputs are available.

### Run tests and inspect the notebooks

```powershell
python -m unittest discover -s tests -v
python -m jupyter lab
```

Run notebooks from the project root, in order:

1. [01_dataset_audit.ipynb](notebooks/01_dataset_audit.ipynb)
2. [02_data_cleaning.ipynb](notebooks/02_data_cleaning.ipynb)
3. [03_exploratory_analysis.ipynb](notebooks/03_exploratory_analysis.ipynb)
4. [04_stock_performance.ipynb](notebooks/04_stock_performance.ipynb)
5. [05_risk_volatility.ipynb](notebooks/05_risk_volatility.ipynb)
6. [06_correlation_statistics.ipynb](notebooks/06_correlation_statistics.ipynb)
7. [07_technical_indicators.ipynb](notebooks/07_technical_indicators.ipynb)
8. [08_predictive_modelling.ipynb](notebooks/08_predictive_modelling.ipynb)
9. [09_model_evaluation.ipynb](notebooks/09_model_evaluation.ipynb)
10. [10_india_vs_us_analysis.ipynb](notebooks/10_india_vs_us_analysis.ipynb)

The cleaning and later India notebooks require the processed dataset; run the preparation script or notebook 02 first. Notebook 01 also inspects `train-00000.parquet`, which is not an input to the main pipeline. Notebook 10 reports input readiness; use the comparison script for the reproducible cross-market outputs.

## Reports and documentation

- [Comprehensive project report](reports/comprehensive_project_report.md)
- [Exploratory analysis](reports/exploratory_analysis_report.md), [risk and performance](reports/risk_performance_report.md), and [model evaluation](reports/ml_evaluation_report.md)
- [Selected-stock India–US comparison](reports/comparative_market_report.md)
- [Dataset audit](reports/dataset_audit_report.md)
- [Data sources](docs/DATA_SOURCES.md), [data dictionary](docs/DATA_DICTIONARY.md), [methodology](docs/METHODOLOGY.md), [key findings](docs/KEY_FINDINGS.md), and [limitations](docs/LIMITATIONS.md)
- [US data audit](docs/US_DATA_AUDIT.md) and [macroeconomic data audit](docs/MACRO_DATA_AUDIT.md)

Pipeline reports and tables are derived outputs and will be regenerated when the analysis scripts run. Do not edit downloaded raw Parquet files in place.

## Limitations and academic disclaimer

The original annual India files have undocumented provenance and adjustment/corporate-action treatment. Cross-market results use supplementary Yahoo adjusted closes rather than those annual prices. Selected stocks are not representative market indices; survivorship and ticker continuity remain concerns. FX alignment is a documented proxy, and macro correlations are based on a very small annual sample. A single chronological model evaluation does not establish predictive skill. See [limitations](docs/LIMITATIONS.md) for the full list.

FinSight is for educational and research use. Historical measurements and model outputs are not investment, tax, or legal advice and do not guarantee future results. The MIT license covers the project code only; downloaded datasets remain subject to their respective terms.
