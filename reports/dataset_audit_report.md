# FinSight Dataset Audit Report

**Audit scope:** Existing workspace files only  
**Audit date:** 2026-11-19  
**Result:** Original downloaded data was read-only during this audit.

> **Current status:** The initial audit below preceded the later acquisitions recorded at the end of this report. The workspace now also has Yahoo Finance US histories, separate Yahoo adjusted-close histories for nine Indian symbols, USD/INR, and World Bank CPI/GDP inputs. Those supplementary files do not resolve the original annual files' provenance or price basis.

## Executive summary

At the initial audit, the workspace contained 11 Parquet files (257,211,483 bytes; about 245.30 MiB) under `data/raw/india/stocks/`:

- Ten annual files, `nse_2016.parquet` through `nse_2025.parquet`, containing 4,597,797 daily records in total.
- `train-00000.parquet`, containing 7,969,510 records. Its timestamps mix midnight records and intraday timestamps, and its price values do not consistently match the annual NSE files. Its source, exchange, and price-adjustment convention are undocumented.

The annual NSE files are a sound starting point for Indian daily stock analysis after filtering to the appropriate equity series and documenting adjustment limitations. No US stock dataset, USD/INR exchange-rate data, or macroeconomic dataset was found. Do not combine the separate shard with the annual files until its cadence and price basis have been reconciled.

## Workspace inventory and annual-file coverage

The ten annual files all have the same 16-column schema. Their annual date ranges cover each named calendar year; market-wide observed trading dates range from 245 to 252 per year. Calendar coverage was checked against the records, but not against an official exchange holiday/session calendar.

| File | Size (MiB) | Rows | Columns | Observed dates | Unique symbols |
|---|---:|---:|---:|---|---:|
| `nse_2016.parquet` | 9.63 | 383,076 | 16 | 2016-01-01–2016-12-30 | 1,708 |
| `nse_2017.parquet` | 9.99 | 396,376 | 16 | 2017-01-02–2017-12-29 | 1,747 |
| `nse_2018.parquet` | 10.39 | 406,387 | 16 | 2018-01-01–2018-12-31 | 1,766 |
| `nse_2019.parquet` | 10.10 | 408,521 | 16 | 2019-01-01–2019-12-31 | 1,807 |
| `nse_2020.parquet` | 10.78 | 428,336 | 16 | 2020-01-01–2020-12-31 | 1,865 |
| `nse_2021.parquet` | 11.28 | 445,386 | 16 | 2021-01-01–2021-12-31 | 2,029 |
| `nse_2022.parquet` | 12.27 | 481,855 | 16 | 2022-01-03–2022-12-30 | 2,146 |
| `nse_2023.parquet` | 12.91 | 505,879 | 16 | 2023-01-02–2023-12-29 | 2,313 |
| `nse_2024.parquet` | 15.15 | 547,291 | 16 | 2024-01-01–2024-12-31 | 2,437 |
| `nse_2025.parquet` | 16.42 | 594,690 | 16 | 2025-01-01–2025-12-31 | 2,681 |
| `train-00000.parquet` | 126.38 | 7,969,510 | 8 | See shard findings | 3,182 |

Across the annual files, 3,512 distinct symbols appear in the union. An observed date gap of up to five calendar days occurs in some annual files; weekends and exchange holidays are expected contributors. Verifying missing *trading sessions* requires an authoritative calendar and is not established by this file-only audit.

## Schemas and field interpretation

Parquet physical/logical types below are from file metadata. Field descriptions are inferred from names; the files do not provide a data dictionary or source metadata.

### Annual NSE files (16 columns)

| Column(s) | Parquet type | Likely meaning |
|---|---|---|
| `date` | `date32[day]` | Session date |
| `symbol`, `series`, `isin`, `name` | `large_string` | Instrument ticker, exchange series, ISIN, and display name |
| `open`, `high`, `low`, `close`, `last`, `prev_close` | `double` | Session OHLC, last traded, and previous close prices |
| `volume` | `int64` | Traded volume; unit is not documented |
| `turnover` | `double` | Turnover; currency/unit is not documented |
| `trades` | `int64` | Trade count |
| `year` | `int32` | Calendar year |
| `month` | `int8` | Calendar month |

Observed `series` values are `EQ`, `BE`, and `BZ`. The annual files contain daily OHLC and volume fields. They do **not** contain an adjusted-close field or corporate-action adjustment factors. Whether the reported prices have any source-side adjustments is undocumented; treat that basis as unknown.

### `train-00000.parquet` (8 columns)

| Column | Parquet type | Likely meaning |
|---|---|---|
| `symbol` | `string` | Instrument ticker/label |
| `timestamp` | `timestamp[us, tz=UTC]` | Timestamp; rows include midnight and intraday times |
| `open`, `high`, `low`, `close` | `float` | OHLC prices |
| `volume`, `oi` | `int64` | Volume and likely open interest; units/semantics are undocumented |

There is no exchange, instrument-name, frequency, currency, or adjustment metadata in this shard.

## Data-quality findings

| Check | Annual NSE files | `train-00000.parquet` |
|---|---:|---:|
| Null values | 0 in all columns | 0 in all columns |
| Duplicate records by natural key | 0 for (`date`, `symbol`, `series`) | 0 for (`symbol`, `timestamp`) |
| Exact duplicate rows | 0 | 0 (the natural key is unique) |
| Nonpositive OHLC/price values | 0 | Open: 892; high: 868; low: 919; close: 743 |
| OHLC relationship violations | 0 | 2,486 rows |
| Zero volume | 0 | 507,541 rows |
| Negative volume | 0 | 1 |

The annual NSE files are internally consistent on these checks. In the shard, the counts of nonpositive price values can overlap; zero-volume observations may include indices or nontrading instruments and need classification rather than blanket deletion. The negative volume, nonpositive prices, and OHLC violations require investigation before analysis.

## Separate-shard investigation

The shard spans UTC timestamps from `1999-12-31 18:30` to `2026-11-12 18:30`; converting to India time gives local dates `2000-01-01` through `2026-11-13`. It contains 3,182 symbols, including India-market-looking stock and index labels such as `RELIANCE`, `HDFCBANK`, and `NIFTY 100`. None of the requested US tickers (`AAPL`, `MSFT`, `NVDA`, `AMZN`, `JPM`, `WMT`, `XOM`, `TSLA`, `JNJ`, `BAC`) were present.

Cadence is mixed: 6,969,202 rows have local time `00:00:00`, while 1,000,308 rows have other times; 1,613 symbols have at least one non-midnight timestamp. The other timestamps include minute-level values such as `09:15` and `09:16`. This cannot be treated as a uniformly daily dataset without separating and validating observations by frequency.

The shard has no source or exchange identifier, so its India-market appearance is suggestive, not proof of provenance. Price values also disagree with the annual files for the same symbol/date: for example, `HDFCBANK` on 2016-01-01 has close 1,088.75 in the annual file and 272.20 in the shard. This may reflect different adjustment/source conventions, but the cause is not documented. Do not merge or compare these prices until their provenance and adjustment basis are resolved.

## Requested Indian-stock availability

All ten requested Indian tickers are present in the annual files in `EQ` series for every year 2016–2025: `RELIANCE`, `TCS`, `INFY` (Infosys), `HDFCBANK`, `ICICIBANK`, `SBIN` (SBI), `ITC`, `ONGC`, `WIPRO`, and `TATAMOTORS`.

Nine requested tickers have a row for every market-wide date in each annual file. `TATAMOTORS` has 202 rows in 2025 and ends on 2025-10-23. Related symbols appear later: `TMPV` (`TATA MOTORS PASS VEH LTD`) begins on 2025-10-24; `TMCV` appears in `BE` from 2025-11-12 through 2025-11-25 and in `EQ` from 2025-11-26 through year-end. These are not automatically interchangeable with the former ticker; corporate-action and entity mapping must be researched before constructing a continuous series.

## Suitability and remaining data requirements

### Suitable with caveats

- The annual NSE files provide the requested 2016–2025 daily Indian stock OHLCV history, with date, security identifiers, series, turnover, and trade counts.
- Use the `EQ` series for a primary listed-equity comparison unless a research question explicitly requires other series.
- Preserve the raw files. Record any filtering, symbol mapping, adjustment, or invalid-value treatment in subsequent processing.
- The annual data does not establish total-return performance. Obtain or calculate a documented corporate-action-adjusted series before interpreting long-horizon returns, risk, or technical indicators.

### Inputs missing at the initial audit

The following items were missing when this audit began. The US stock, USD/INR, and macroeconomic inputs were subsequently acquired; see the dated follow-up sections below. Comparable benchmark-index files and confirmed provenance for the original Parquets remain unresolved.

- **US stock data:** No US dataset or requested US ticker was found. Acquire independently (the requested `yfinance` source is a candidate) and document ticker history, adjustments, and corporate actions; do not treat the shard as US data.
- **Currency:** No USD/INR series was found. It is required for currency-adjusted India–US comparisons.
- **Macroeconomic data:** No Indian or US macroeconomic indicators were found. Select documented sources/series that match the research questions and time frequency.
- **Comparable market indices:** Annual files are security-level and do not provide documented benchmark-index data. The shard has index-like symbols, but its source and price basis are unresolved. Obtain consistent, documented Indian and US benchmark series if index-level comparison is required.
- **Provenance and licenses:** No source, download date, data dictionary, or license information was present. Record this for every retained dataset before publishing the project.

## Audit conclusion

The annual files cover the named calendar years 2016–2025 and passed the documented basic row-level checks. They support descriptive India daily analysis with the price-basis caveat. The separate shard remains quarantined until its mixed cadence, anomalies, source, and conflicting price basis are resolved.

The later follow-ups added US stock histories, supplementary adjusted-price histories, USD/INR, and World Bank CPI/GDP series. They enable the selected-stock comparison documented below, but do not validate the source or adjustment basis of the original annual files. Provenance, corporate-action treatment, comparable index data, and the limitations of selected stocks remain open issues.

## Follow-up: US stock acquisition (2026-11-19)

After the initial audit, the user approved downloading the requested US tickers. `scripts/download_us_data.py` retrieved all ten tickers from Yahoo Finance using yfinance 0.2.66 for the interval 2016-01-01 inclusive to 2026-01-01 exclusive. The files are in `data/raw/usa/stocks/`; this follow-up did not modify any original India file.

| Ticker | File size (bytes) | Rows | First date | Last date | Nonzero dividend rows | Nonzero split rows |
|---|---:|---:|---|---|---:|---:|
| AAPL | 133,849 | 2,514 | 2016-01-04 | 2025-12-31 | 40 | 1 |
| AMZN | 134,158 | 2,514 | 2016-01-04 | 2025-12-31 | 0 | 1 |
| BAC | 116,043 | 2,514 | 2016-01-04 | 2025-12-31 | 40 | 0 |
| JNJ | 123,480 | 2,514 | 2016-01-04 | 2025-12-31 | 40 | 0 |
| JPM | 129,526 | 2,514 | 2016-01-04 | 2025-12-31 | 40 | 0 |
| MSFT | 133,014 | 2,514 | 2016-01-04 | 2025-12-31 | 40 | 0 |
| NVDA | 136,594 | 2,514 | 2016-01-04 | 2025-12-31 | 40 | 2 |
| TSLA | 135,130 | 2,514 | 2016-01-04 | 2025-12-31 | 0 | 2 |
| WMT | 129,390 | 2,514 | 2016-01-04 | 2025-12-31 | 40 | 1 |
| XOM | 122,745 | 2,514 | 2016-01-04 | 2025-12-31 | 40 | 0 |

Each file contains `date`, raw `open/high/low/close`, `adj_close`, `volume`, `dividends`, `stock_splits`, `symbol`, `market`, and `currency`; all were tagged `USA`/`USD`. The verified files had no null cells, nonpositive OHLC values, or OHLC relationship violations. Each has 2,514 unique dated observations. Nonzero split/dividend rows are source event records, not evidence that the full corporate-action history is exhaustive.

At this point in the acquisition sequence, the US stock files were available, but India–US performance was not yet directly comparable: supplementary Indian adjusted-price histories, USD/INR, and macroeconomic inputs had not yet been acquired. Those later inputs and the resulting analysis are recorded in the next follow-up section.

## Follow-up: comparison and macro data (2026-11-19)

Separate Yahoo Finance adjusted-close histories were retrieved for nine requested Indian stocks (`RELIANCE`, `TCS`, `INFY`, `HDFCBANK`, `ICICIBANK`, `SBIN`, `ITC`, `ONGC`, `WIPRO`) and the `USDINR=X` exchange-rate series. Each Indian file contains 2,470 observations dated 2016-01-01 through 2025-12-31. The exchange-rate file contains 2,602 observations over that same date range. These auxiliary histories are stored separately and do not replace the original annual NSE files. Yahoo did not return the `TATAMOTORS.NS` symbol; the newer TMPV history was not assumed equivalent and was excluded.

The supplementary Yahoo raw closes materially differ from the annual NSE `EQ` closes for some of the same symbol/date pairs, indicating different source or adjustment conventions. For example, on 2016-01-01, annual NSE `RELIANCE` close is 1,015.35 while Yahoo's `RELIANCE.NS` close is 232.09; Yahoo's adjusted close is 219.00. Therefore, the cross-market comparison uses Yahoo adjusted closes for both countries, not a mixture of annual NSE prices and Yahoo prices. The original Indian price basis remains unresolved.

World Bank annual CPI inflation and GDP growth series were retrieved for India and the USA for 2016–2025 (40 country/year/indicator rows). The API update date recorded in the response is 2026-11-11. The USA 2025 CPI value is missing and is not imputed. See `docs/MACRO_DATA_AUDIT.md` for indicator and missingness details.

The selected-stock comparison and annual macro correlations are generated in [the comparative report](comparative_market_report.md). They are exploratory: the stock universe is not a market index, the macro sample has only 9–10 annual observations, and no causal inference is made. The source definitions are available from the [World Bank CPI series](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG) and [GDP growth series](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG); Yahoo downloads use the [yfinance client](https://github.com/ranaroussi/yfinance).
