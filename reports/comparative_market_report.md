# India–US Selected-Stock Comparison

## Data and scope

This comparison uses Yahoo Finance adjusted-close observations for nine Indian symbols (RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, SBIN, ITC, ONGC, WIPRO) and ten US symbols. `TATAMOTORS` is excluded because Yahoo Finance did not return its requested ticker; the replacement TMPV history is not assumed to be the same continuous security. Data cover the downloaded 2016–2025 interval. The Indian prices are auxiliary Yahoo histories, not the original NSE file series. The download client is [yfinance](https://github.com/ranaroussi/yfinance); review applicable Yahoo Finance terms before redistribution.

The adjusted close is used for both universes to account for provider-reported splits/dividends. This basis is provider-defined and is not independently verified. USD/INR is Yahoo Finance `USDINR=X`, interpreted as INR per USD. For each Indian market date, the most recent FX observation strictly before that date is used, avoiding use of a same-date FX close that may occur after the Indian equity close. The US adjusted close is already USD-denominated.

## Results

- Median per-stock annualized return in USD terms: India 11.20%; USA 21.35%.
- Median per-stock annualized volatility in USD terms: India 26.66%; USA 28.46%.
- Equal-weight daily portfolio paths use only dates on which both selected universes have observations; the shared-date period is 2016-01-04 to 2025-12-31. Returns within each universe are the arithmetic mean across that universe's available selected stocks on a shared date.
- The [per-stock results](tables/cross_market_stock_metrics.csv), [selected-universe summary](tables/cross_market_summary.csv), and [shared-date daily series](tables/cross_market_equal_weight_usd.csv) contain detailed metrics. Annualized return uses elapsed calendar days; annualized volatility uses 252 sessions.

## Interpretation and limitations

These are comparisons of selected surviving tickers, not market indices. Stock selection is not capitalization weighted and does not address survivorship bias. Yahoo adjusted closes and FX history may be revised, and the India supplementary series differ from the original NSE files. The USD/INR alignment uses the previous available FX observation, not an official fixing. The local-currency and USD-basis metrics are both retained in the tables.

Exploratory correlations of annual equal-weight local-currency returns with World Bank annual indicators:

- INDIA vs FP.CPI.TOTL.ZG: n=10, Pearson r=-0.021 (p=0.954), Spearman rho=0.079 (p=0.829).
- INDIA vs NY.GDP.MKTP.KD.ZG: n=10, Pearson r=-0.046 (p=0.901), Spearman rho=-0.200 (p=0.580).
- USA vs FP.CPI.TOTL.ZG: n=9, Pearson r=-0.619 (p=0.075), Spearman rho=-0.317 (p=0.406).
- USA vs NY.GDP.MKTP.KD.ZG: n=10, Pearson r=-0.143 (p=0.694), Spearman rho=-0.042 (p=0.907).

Sample sizes are small; p-values are unadjusted and do not imply causation.

Annual indicator inputs are from the [World Bank CPI series](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG) and [GDP growth series](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG); see the [macro data audit](../docs/MACRO_DATA_AUDIT.md). Method details are in the [project methodology](../docs/METHODOLOGY.md).

Results are descriptive, not causal, not financial advice, and not a forecast of future performance.
