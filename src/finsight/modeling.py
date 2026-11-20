"""Leakage-conscious chronological next-session return forecasting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class ForecastResult:
    """Out-of-sample metrics and predictions for a single stock."""

    metrics: pd.DataFrame
    predictions: pd.DataFrame
    selected_model: str
    validation_metrics: pd.DataFrame
    split_sizes: dict[str, int]


def make_next_return_features(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Construct past-only features and the next-session return target."""
    required = {"date", "close"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Required columns: {sorted(required)}")
    if "symbol" in frame and frame["symbol"].nunique() != 1:
        raise ValueError("Pass data for exactly one symbol")

    data = frame.sort_values("date").copy()
    if data["date"].duplicated().any():
        raise ValueError("Input must have one observation per date")
    close = pd.to_numeric(data["close"], errors="raise").astype(float)
    if (close <= 0).any():
        raise ValueError("Close prices must be positive")
    returns = close.pct_change(fill_method=None)
    data["return_lag_1"] = returns
    data["return_lag_2"] = returns.shift(1)
    data["return_lag_5"] = returns.shift(4)
    data["volatility_5"] = returns.rolling(5, min_periods=5).std()
    data["momentum_5"] = close.pct_change(5, fill_method=None)
    data["sma_gap_20"] = close.div(close.rolling(20, min_periods=20).mean()).sub(1.0)
    data["sma_gap_50"] = close.div(close.rolling(50, min_periods=50).mean()).sub(1.0)
    features = [
        "return_lag_1",
        "return_lag_2",
        "return_lag_5",
        "volatility_5",
        "momentum_5",
        "sma_gap_20",
        "sma_gap_50",
    ]
    if "volume" in data:
        volume = pd.to_numeric(data["volume"], errors="coerce")
        data["volume_change"] = volume.pct_change(fill_method=None).replace(
            [np.inf, -np.inf], np.nan
        )
        features.append("volume_change")

    data["target_return"] = returns.shift(-1)
    data["target_date"] = data["date"].shift(-1)
    data = data.dropna(subset=features + ["target_return", "target_date"]).reset_index(drop=True)
    if len(data) < 100:
        raise ValueError("At least 100 complete feature/target rows are required")
    return data, features


def _models() -> dict[str, object]:
    return {
        "Linear Regression": LinearRegression(),
        "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "Random Forest": RandomForestRegressor(
            n_estimators=100,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=100,
            max_depth=2,
            learning_rate=0.03,
            loss="huber",
            random_state=42,
        ),
    }


def _score(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    mse = mean_squared_error(actual, predicted)
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "mse": float(mse),
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(actual, predicted)),
    }


def evaluate_forecasts(frame: pd.DataFrame) -> ForecastResult:
    """Compare zero-return baseline and regressors using chronological splits."""
    data, feature_columns = make_next_return_features(frame)
    n = len(data)
    train_end = int(n * 0.60)
    validation_end = int(n * 0.80)
    if train_end < 30 or validation_end - train_end < 20 or n - validation_end < 20:
        raise ValueError("Insufficient rows for chronological train/validation/test splits")

    X = data[feature_columns]
    y = data["target_return"].to_numpy(dtype=float)
    candidates = _models()
    validation_rows: list[dict[str, float | str]] = []
    for name, model in candidates.items():
        model.fit(X.iloc[:train_end], y[:train_end])
        predictions = model.predict(X.iloc[train_end:validation_end])
        validation_rows.append({"model": name, **_score(y[train_end:validation_end], predictions)})
    validation = pd.DataFrame(validation_rows).sort_values("mae").reset_index(drop=True)
    selected_model = str(validation.iloc[0]["model"])

    fit_end = validation_end
    test_actual = y[fit_end:]
    test_dates = data.loc[fit_end:, "target_date"].to_numpy()
    output_rows: list[pd.DataFrame] = []
    metric_rows: list[dict[str, float | str]] = []
    baseline_prediction = np.zeros_like(test_actual)
    metric_rows.append({"model": "Zero-return baseline", **_score(test_actual, baseline_prediction)})
    output_rows.append(
        pd.DataFrame(
            {
                "date": test_dates,
                "actual_return": test_actual,
                "predicted_return": baseline_prediction,
                "model": "Zero-return baseline",
            }
        )
    )

    for name, model in candidates.items():
        model.fit(X.iloc[:fit_end], y[:fit_end])
        predicted = model.predict(X.iloc[fit_end:])
        metric_rows.append({"model": name, **_score(test_actual, predicted)})
        output_rows.append(
            pd.DataFrame(
                {
                    "date": test_dates,
                    "actual_return": test_actual,
                    "predicted_return": predicted,
                    "model": name,
                }
            )
        )
    return ForecastResult(
        metrics=pd.DataFrame(metric_rows).sort_values("mae").reset_index(drop=True),
        predictions=pd.concat(output_rows, ignore_index=True),
        selected_model=selected_model,
        validation_metrics=validation,
        split_sizes={
            "train": train_end,
            "validation": validation_end - train_end,
            "test": n - validation_end,
        },
    )
