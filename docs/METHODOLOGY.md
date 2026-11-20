# Methodology

## Research scope and inputs

The primary local dataset consists of ten annual India Parquet files for 2016–2025. The analysis retains `series == "EQ"` and the requested Indian symbols. Dates are treated as observed session dates; OHLC and volume are not rescaled. The mixed-cadence `train-00000.parquet` shard is excluded pending provenance, cadence, and price-basis reconciliation. See the [dataset audit](../reports/dataset_audit_report.md) and [data-source register](DATA_SOURCES.md).

Cross-market analysis, when its optional inputs are present, uses separate Yahoo Finance adjusted-close files for nine Indian and ten US symbols, plus `USDINR=X`. Macro correlations use annual World Bank CPI inflation and GDP growth. Neither supplementary stock histories nor macro series replace the original annual India files.

## Preparation and validation

The preparation path checks required fields, nulls in required values, nonpositive OHLC, OHLC ordering, negative volume, and duplicate (`date`, `symbol`, `series`) keys. It raises a descriptive error instead of silently dropping invalid rows. The processed all-`EQ` Parquet is a separate output; raw files are not modified.

## Returns and performance

Daily simple returns use consecutive observed closes by symbol:

\[
r_t = \frac{P_t}{P_{t-1}} - 1
\]

Monthly and calendar-year returns use the last observed close in each period. Missing sessions are not filled with synthetic prices. Because the annual files' corporate-action treatment is undocumented, their returns are not described as verified total returns.

## Risk

Risk measures use 252 sessions per year. Annualized volatility is the sample standard deviation of daily returns multiplied by \(\sqrt{252}\). Sharpe subtracts a zero daily risk-free rate by default. Downside deviation is the root-mean-square of negative daily returns, annualized by \(\sqrt{252}\). Maximum drawdown is calculated from compounded simple returns and the prior observed wealth peak.

## Correlation and statistical tests

Correlation matrices use date-aligned daily returns and require at least 30 paired observations. Pearson and Spearman coefficients are available. The selected-pair significance test reports two-sided p-values. Augmented Dickey–Fuller results use statsmodels with automatic AIC lag selection; the null hypothesis is a unit root. These tests do not establish causal or economic explanations.

## Technical indicators

The implementation calculates 20- and 50-observation simple moving averages; 12- and 26-span exponential moving averages; a 9-span MACD signal; RSI with a 14-session exponentially smoothed gain/loss; and 20-session Bollinger Bands using two population standard deviations. Calculations use current and past observations only. Indicators describe historical prices and are not validated trading signals.

## Forecast design

The example target is the next observed session's simple return. Features use information available at or before the current close: lagged returns, trailing volatility and momentum, moving-average gaps, and prior/current observed volume change where volume is present. Rows remain chronological. A 60% / 20% / 20% train/validation/test split is used; validation MAE selects a candidate, and models are refit on train plus validation before one final test evaluation. A zero-return baseline is included. MAPE is omitted because returns can be zero or close to zero. See [model evaluation](MODEL_EVALUATION.md).

## Cross-market and macro analysis

The selected-stock comparison uses Yahoo adjusted closes for nine Indian symbols with returned histories and ten US symbols. Tata Motors is excluded because Yahoo did not return the requested legacy symbol; TMPV is not assumed to be the same continuous security. The supplementary prices are not merged into the annual NSE series.

`USDINR=X` is interpreted as INR per USD. Each Indian equity session uses the latest FX observation strictly before its date (`allow_exact_matches=False`), avoiding a same-date FX close that could occur after the equity close. A seven-day maximum age is required by the loader. US adjusted closes are USD-denominated. Metrics are retained in native currency and, for the comparison, USD. The median stock results summarize selected tickers, not market indices.

Equal-weight daily portfolio paths use shared observed dates and the arithmetic mean of available selected-stock returns within each market. Annual macro analysis compounds these daily local-currency portfolio returns by year and aligns them with World Bank annual CPI and GDP growth by country and year. The sample has at most ten years (and nine US CPI pairs because the 2025 value is missing); reported p-values are unadjusted. Results are exploratory and correlational.
