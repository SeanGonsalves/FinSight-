# US Stock Data Audit

| Item | Recorded value |
|---|---|
| Retrieved | 2026-11-19 |
| Retrieval client | yfinance 0.2.66 |
| Provider | Yahoo Finance |
| Requested interval | 2016-01-01 inclusive to 2026-01-01 exclusive |
| Storage | `data/raw/usa/stocks/`, one Parquet file per ticker |

## Coverage

| Ticker | Rows | First date | Last date | File size (bytes) | Nonzero dividend rows | Nonzero split rows |
|---|---:|---|---|---:|---:|---:|
| AAPL | 2,514 | 2016-01-04 | 2025-12-31 | 133,849 | 40 | 1 |
| AMZN | 2,514 | 2016-01-04 | 2025-12-31 | 134,158 | 0 | 1 |
| BAC | 2,514 | 2016-01-04 | 2025-12-31 | 116,043 | 40 | 0 |
| JNJ | 2,514 | 2016-01-04 | 2025-12-31 | 123,480 | 40 | 0 |
| JPM | 2,514 | 2016-01-04 | 2025-12-31 | 129,526 | 40 | 0 |
| MSFT | 2,514 | 2016-01-04 | 2025-12-31 | 133,014 | 40 | 0 |
| NVDA | 2,514 | 2016-01-04 | 2025-12-31 | 136,594 | 40 | 2 |
| TSLA | 2,514 | 2016-01-04 | 2025-12-31 | 135,130 | 0 | 2 |
| WMT | 2,514 | 2016-01-04 | 2025-12-31 | 129,390 | 40 | 1 |
| XOM | 2,514 | 2016-01-04 | 2025-12-31 | 122,745 | 40 | 0 |

## Schema and quality checks

The files contain `date`, raw `open`, `high`, `low`, and `close`, `adj_close`, `volume`, `dividends`, `stock_splits`, and identifying fields (`symbol`, `market`, and `currency`). Values were tagged as `market=USA` and `currency=USD`. Each file contains 2,514 unique date records. The audit found no null cells, nonpositive OHLC values, or OHLC relationship violations.

Nonzero dividend and split counts describe the returned records in this download; they do not prove that the provider's full action history is exhaustive. Review raw-versus-adjusted price behavior before deciding which field is suitable for a particular analysis.

## Comparability and provenance

Supplementary Yahoo adjusted-close histories for nine Indian stocks, a USD/INR series, and World Bank CPI/GDP inputs were acquired separately; the original annual India price basis remains undocumented and is not mixed with these histories. The selected-stock comparison and conversion assumptions are in the [comparative report](../reports/comparative_market_report.md) and [methodology](METHODOLOGY.md); the macro series are described in the [macro audit](MACRO_DATA_AUDIT.md).

Yahoo data availability, terms, and historical values can change. Before redistribution, review the [yfinance project information](https://github.com/ranaroussi/yfinance) and applicable Yahoo Finance terms. The download script is [download_us_data.py](../scripts/download_us_data.py); rerunning it replaces files with the same names.
