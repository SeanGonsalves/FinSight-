# Exploratory Analysis Report

## Scope and data

This report uses the annual India Parquet files, filtered to the `EQ` series and the requested Indian tickers. The processed dataset contains 4,130,255 `EQ` rows across all symbols; this analysis uses 24,733 selected-stock rows across 10 symbols. The observed selected-stock date range is 2016-01-01 to 2025-12-31.

## Observations

- Selected symbols: HDFCBANK, ICICIBANK, INFY, ITC, ONGC, RELIANCE, SBIN, TATAMOTORS, TCS, WIPRO.
- The source supplies daily OHLC, volume, turnover, and trade-count fields. This report does not infer a benchmark or market-wide return from security-level observations.
- [Annual-file coverage](tables/nse_yearly_coverage.csv) is listed in the result tables; price and volume charts are in `figures/eda/`.
- The source has no documented adjusted-close or corporate-action factor. Normalized prices and returns therefore inherit the annual files' undocumented price basis.

## Conclusion

The selected universe supports descriptive daily-stock analysis for the audited period. Resolve corporate-action treatment, listed-entity continuity, and security-level coverage before interpreting long-horizon comparisons as total returns. See the [dataset audit](dataset_audit_report.md) and [methodology](../docs/METHODOLOGY.md).
