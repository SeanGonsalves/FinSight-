# Model Evaluation

## Forecast target and features

The example forecasts the next observed session's close-to-close simple return for one Indian symbol. Features at time \(t\) are built from information available at or before that observation: lagged returns, trailing volatility and momentum, moving-average gaps, and volume change when volume is available. The response is the next observed return. The underlying annual India price basis is not verified as corporate-action adjusted.

## Candidate models and baseline

The comparison includes a zero-return baseline, Linear Regression, Ridge regression with standardization, Random Forest regression, and Gradient Boosting regression. Models are scored with mean absolute error (MAE), mean squared error (MSE), root mean squared error (RMSE), and \(R^2\). MAPE is omitted because returns may be zero or close to zero.

## Chronological selection and test procedure

Rows remain in time order; they are not randomly shuffled. The first 60% is training data, the next 20% validation data, and the final 20% held-out test data. Validation MAE selects the candidate. After selection, each candidate is refit on the combined training and validation rows and evaluated once on the final test interval. The test data do not determine the selected model.

The most recent generated results are in [the model evaluation report](../reports/ml_evaluation_report.md), [model comparison table](../reports/tables/model_comparison.csv), and [validation table](../reports/tables/model_validation.csv). The chosen validation candidate need not have the lowest test error; test results must not be used to retroactively select a model.

## Interpretation limits

A single temporal split does not establish stable forecasting skill. Visual fit or a favorable metric does not guarantee future performance. Results may be affected by changing regimes, unadjusted or inconsistently adjusted prices, feature selection, transaction costs, liquidity, data revisions, and survivorship bias. This is a research example, not an investment recommendation or financial advice.

For the full feature and split specification, see [methodology](METHODOLOGY.md).
