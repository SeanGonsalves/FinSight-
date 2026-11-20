# Macroeconomic Data Audit

| Item | Recorded value |
|---|---|
| Retrieved | 2026-11-19 |
| Provider | World Bank Indicators API |
| API metadata update date | 2026-11-11 |
| Requested period | Annual observations, 2016–2025 |
| Local file | `data/raw/macroeconomic/world_bank_annual_2016_2025.parquet` |

## Indicators and coverage

| Indicator code | Series | Countries | Official series page |
|---|---|---|---|
| `FP.CPI.TOTL.ZG` | Inflation, consumer prices (annual %) | India (`IND`), United States (`USA`) | [World Bank CPI indicator](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG) |
| `NY.GDP.MKTP.KD.ZG` | GDP growth (annual %) | India (`IND`), United States (`USA`) | [World Bank GDP growth indicator](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG) |

The retrieved Parquet contains 40 country/year/indicator rows. Each of the four country/indicator pairs has ten year records, but the value for US CPI in 2025 is missing. The analysis retains that missing value and does not impute it; consequently, that correlation uses nine paired years. The source definitions and API are documented by the [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation).

## Use in FinSight

Annual macro values are aligned by country and year with annual equal-weight, local-currency returns for each selected-stock universe. Pearson and Spearman correlations are reported with paired observation counts and p-values. With only 9–10 annual observations, tests have low power; p-values are unadjusted, and the analysis does not show that macroeconomic variables caused stock returns.

The API may revise historical values. Each row preserves the API `source_last_updated` value and the UTC retrieval time. This dataset contains neither policy rates nor monthly observations.

## Reproduction

From the project root, rerun the download with:

```powershell
python scripts/download_macro_data.py
```

This replaces the named local output file. Re-run `python scripts/run_market_comparison.py` or `python scripts/run_analysis.py` to regenerate the derived annual alignment and correlation outputs. Review applicable source terms before redistributing data.
