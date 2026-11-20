# Predictive Model Evaluation

## Target and split

The models predict the next observed session's simple close-to-close return from lagged returns, trailing volatility/momentum, moving-average gaps, and (where available) volume change known at the observation date. Rows remain chronological; split sizes are train=1,456, validation=486, and test=486. Validation MAE selects a candidate. Candidates are then refit on train plus validation before the held-out test evaluation.

The validation-selected candidate was **Linear Regression**. Its test MAE is 0.010876; the zero-return baseline test MAE is 0.010556. The lowest test MAE in the comparison is **Zero-return baseline** (0.010556). Test results are descriptive and must not be used to retroactively select a model.

For the validation-selected model, held-out residual mean is -0.001414 and sample standard deviation is 0.026450. Actual-versus-predicted and residual plots are saved under `figures/modelling/`.

## Metrics and limitations

MAE, MSE, RMSE, and R-squared are in the [model comparison table](tables/model_comparison.csv); validation scores are in [model validation](tables/model_validation.csv). MAPE is omitted because returns can be zero or arbitrarily close to zero, making percentage error unstable. A single historical split does not establish predictive skill. Price adjustments, regime changes, and transaction costs remain limitations; see [model evaluation notes](../docs/MODEL_EVALUATION.md).
