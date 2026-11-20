# Data Dictionary

The source Parquet files do not contain a provider-authored data dictionary. Field meanings below are inferred from names and observed types; verify them against authoritative source metadata before making unit-sensitive claims. The [dataset audit report](../reports/dataset_audit_report.md) records schemas and checks, while the [data-source register](DATA_SOURCES.md) describes provenance limits.

## Annual India files

The ten `nse_YYYY.parquet` files contain 16 columns. The pipeline standardizes column names to lowercase and uses `EQ` records.

| Field | Observed type | Description |
|---|---|---|
| `date` | date | Session date |
| `symbol` | string | Exchange-style symbol |
| `series` | string | Observed values include `EQ`, `BE`, and `BZ` |
| `isin` | string | Security identifier |
| `name` | string | Display name |
| `open`, `high`, `low`, `close` | float64 | Session OHLC prices |
| `last` | float64 | Likely last traded price |
| `prev_close` | float64 | Previous close |
| `volume` | int64 | Traded volume; unit is undocumented |
| `turnover` | float64 | Turnover; currency and unit are undocumented |
| `trades` | int64 | Trade count |
| `year` | int32 | Calendar year |
| `month` | int8 | Calendar month |

These files have no explicit adjusted-close field or corporate-action factor. The data do not establish whether source-side adjustment has already occurred.

## Separate `train-00000.parquet` shard

| Field | Observed type | Description |
|---|---|---|
| `symbol` | string | Instrument label |
| `timestamp` | UTC timestamp, microsecond precision | Timestamp; both midnight and intraday values occur |
| `open`, `high`, `low`, `close` | float32 | OHLC prices |
| `volume` | int64 | Volume; unit is undocumented |
| `oi` | int64 | Possibly open interest; meaning and source are undocumented |

The shard has no source, exchange, currency, frequency, or adjustment metadata. It is inspected by the audit notebook but excluded from the analysis pipeline.

## Supplementary market files

The Yahoo US and Indian histories include `date`, `open`, `high`, `low`, `close`, `adj_close`, `volume`, `dividends`, `stock_splits`, and identifying metadata such as `symbol`, `market`, and `currency` (the exact returned fields depend on the source response). The USD/INR file includes a date and a `close` rate interpreted as INR per USD. The World Bank file is long-form and includes country and indicator codes, year, value, unit, source update date, and retrieval time. See [US data audit](US_DATA_AUDIT.md) and [macro data audit](MACRO_DATA_AUDIT.md).

## Derived measures

| Measure | Definition |
|---|---|
| `daily_return` | Close-to-close simple return, \(P_t/P_{t-1}-1\), calculated separately for each symbol over observed rows |
| `annualized_volatility` | Sample standard deviation of daily returns multiplied by \(\sqrt{252}\) |
| `max_drawdown` | Minimum compounded-wealth drawdown from a prior observed peak |
| `sharpe_ratio` | Mean daily excess return divided by sample daily standard deviation, multiplied by \(\sqrt{252}\); the default daily risk-free rate is zero |
| `target_return` | Next observed session's close-to-close simple return in the forecasting dataset |

Returns from the annual India files inherit their undocumented price basis; the supplementary adjusted-close comparison uses a different source series.
