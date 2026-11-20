# Data Sources and Provenance

This register separates the provider of a data file from the software used to retrieve it. Files stored in `data/raw/` are local inputs and are not changed by the analysis pipeline.

## Primary India Parquet files

The workspace contains `nse_2016.parquet` through `nse_2025.parquet` and `train-00000.parquet` under `data/raw/india/stocks/`. The provider, retrieval date, license, and version of these files are not recorded. Their NSE-like names and symbols do not establish that they came from the [National Stock Exchange of India](https://www.nseindia.com/market-data/archives).

The annual files' schema, coverage, and row-level checks are documented in the [dataset audit report](../reports/dataset_audit_report.md). They contain daily OHLCV-style fields but no explicit adjusted-close or corporate-action factor. The separate shard has undocumented provenance, mixed daily/intraday timestamps, anomalies, and prices that conflict with the annual files. It is excluded from production analysis.

## Yahoo Finance market data

The acquisition scripts call Yahoo Finance through the [`yfinance` package](https://github.com/ranaroussi/yfinance), an open-source client that is not affiliated with or endorsed by Yahoo. Yahoo Finance data availability, returned history, adjustments, and terms may change.

| Dataset | Retrieval script | Stored files | Use |
|---|---|---|---|
| Ten US stock histories, 2016–2025 | [`download_us_data.py`](../scripts/download_us_data.py) | `data/raw/usa/stocks/usa_<ticker>_2016_2025.parquet` | US OHLC, adjusted close when returned, volume, and reported dividend/split fields |
| Nine Indian supplementary histories, 2016–2025 | [`download_comparability_data.py`](../scripts/download_comparability_data.py) | `data/raw/india/yahoo_adjusted/india_yahoo_<symbol>_2016_2025.parquet` | Adjusted-close series for the selected India–US comparison |
| USD/INR, 2016–2025 | [`download_comparability_data.py`](../scripts/download_comparability_data.py) | `data/raw/macroeconomic/usdinr_yahoo_2016_2025.parquet` | FX conversion, interpreted as INR per USD |

The US files were retrieved on 2026-11-19 with yfinance 0.2.66; file-level coverage and checks are in the [US data audit](US_DATA_AUDIT.md). The supplementary Indian files exclude Tata Motors: Yahoo did not return the requested legacy symbol, and the newer TMPV history is not assumed to be continuous-equivalent. These histories are stored separately and do not resolve the original annual files' price basis.

For each Indian equity session, USD conversion uses the most recent FX observation strictly before the session date. This is a conservative alignment convention, not an official fixing.

## World Bank macroeconomic indicators

[`download_macro_data.py`](../scripts/download_macro_data.py) requests annual data for India (`IND`) and the United States (`USA`) from the [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation):

| Indicator code | Series | Official series page |
|---|---|---|
| `FP.CPI.TOTL.ZG` | Inflation, consumer prices (annual %) | [World Bank CPI indicator](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG) |
| `NY.GDP.MKTP.KD.ZG` | GDP growth (annual %) | [World Bank GDP growth indicator](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG) |

The retrieved records include the API's `lastupdated` value and a local UTC retrieval timestamp. The 2025 US CPI observation is missing and remains missing in the analysis. Coverage and other audit details are in [the macro data audit](MACRO_DATA_AUDIT.md). World Bank values can be revised; refresh and re-audit them before reproducing a historical result.

## Storage, use, and redistribution

Raw and processed data paths are ignored by `.gitignore`; a checkout may not include the local files used to produce the checked-in documentation and figures. The downloader scripts explicitly overwrite their named output files when rerun. Respect each provider's terms and licensing conditions. The repository's MIT license applies to project code only and does not grant rights to downloaded data.
