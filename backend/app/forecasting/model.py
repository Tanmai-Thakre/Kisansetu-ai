"""
Phase 3 — Forecasting Model for the Mandi Price Forecasting Agent.

Uses scikit-learn RandomForestRegressor as the primary model.
Falls back to a moving-average baseline when insufficient data exists.

No LLM — pure numerical prediction.
Model evaluation: MAE + RMSE on a chronological test split.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Tuple
import math

from sklearn.ensemble import RandomForestRegressor   # type: ignore
from sklearn.metrics import mean_absolute_error      # type: ignore

from .data_preprocessor import PreparedSeries, MIN_HISTORY_DAYS
from .feature_engineering import (
    build_feature_matrix, _moving_average, MA_SHORT, MA_MEDIUM, MA_LONG, LAG_DAYS
)


# ── Model constants ───────────────────────────────────────────────────────────
RF_PARAMS = {
    "n_estimators": 100,
    "max_depth":    6,
    "random_state": 42,
    "n_jobs":      -1,
}


# ── Metrics ───────────────────────────────────────────────────────────────────

def _rmse(actual: List[float], predicted: List[float]) -> float:
    n = len(actual)
    if n == 0:
        return 0.0
    mse = sum((a - p) ** 2 for a, p in zip(actual, predicted)) / n
    return math.sqrt(mse)


def _mae(actual: List[float], predicted: List[float]) -> float:
    n = len(actual)
    if n == 0:
        return 0.0
    return sum(abs(a - p) for a, p in zip(actual, predicted)) / n


# ── Moving Average baseline ───────────────────────────────────────────────────

class MovingAverageModel:
    """
    Naïve moving-average baseline.
    Forecast = weighted blend of MA_SHORT and MA_MEDIUM on the last observed prices.
    Used when there are not enough records for the RF model.
    """
    def __init__(self):
        self._last_prices: List[float] = []

    def fit(self, series: PreparedSeries) -> None:
        self._last_prices = series.prices[:]

    def predict_one(self, horizon_days: int) -> float:
        """Predict price `horizon_days` ahead using MA extrapolation."""
        prices = self._last_prices[:]
        for _ in range(horizon_days):
            ma_s  = _moving_average(prices, MA_SHORT,  len(prices) - 1)
            ma_m  = _moving_average(prices, MA_MEDIUM, len(prices) - 1)
            # Slight forward drift — blended estimate
            next_p = 0.6 * ma_s + 0.4 * ma_m
            prices.append(next_p)
        return round(prices[-1], 2)

    def evaluate(self, train: PreparedSeries, test: PreparedSeries) -> Dict:
        """Evaluate on the test split using the walk-forward method."""
        preds = []
        prices = train.prices[:]
        for i in range(len(test.prices)):
            ma = _moving_average(prices, MA_SHORT, len(prices) - 1)
            preds.append(ma)
            prices.append(test.prices[i])   # add actual for next step
        mae_val  = _mae(test.prices, preds)
        rmse_val = _rmse(test.prices, preds)
        return {"mae": round(mae_val, 2), "rmse": round(rmse_val, 2), "model": "MovingAverage"}


# ── Random Forest model ───────────────────────────────────────────────────────

def _build_features_for_prediction(
    prices:   List[float],
    arrivals: List[float],
    dates,
) -> List[float]:
    """Build a single feature vector from the END of the current series."""
    import math
    i = len(prices) - 1
    max_arrival = max(arrivals) if arrivals else 1.0
    feats: List[float] = []

    for lag in LAG_DAYS:
        idx = i - lag
        feats.append(prices[idx] if idx >= 0 else prices[0])

    feats.append(_moving_average(prices, MA_SHORT,  i))
    feats.append(_moving_average(prices, MA_MEDIUM, i))
    feats.append(_moving_average(prices, MA_LONG,   i))

    # Volatility
    def _vol(win):
        start = max(0, i - win + 1)
        sub = prices[start: i + 1]
        if len(sub) < 2:
            return 0.0
        mean = sum(sub) / len(sub)
        return math.sqrt(sum((x - mean) ** 2 for x in sub) / len(sub))
    feats.append(_vol(MA_SHORT))
    feats.append(_vol(MA_MEDIUM))

    # Momentum
    feats.append(prices[i] - prices[max(0, i - MA_SHORT)])
    feats.append(prices[i] - prices[max(0, i - MA_MEDIUM)])

    # Arrival
    feats.append(arrivals[i] / max_arrival if max_arrival > 0 else 0.0)

    # Day-of-week
    dow = dates[i].weekday()
    feats.append(math.sin(2 * math.pi * dow / 7))
    feats.append(math.cos(2 * math.pi * dow / 7))

    return feats


class PriceForecastModel:
    """
    RandomForest-based price forecasting model.
    Trained on the full available history and predicts iteratively
    for 7, 15, and 30 day horizons.
    """

    def __init__(self):
        self._rf:   Optional[RandomForestRegressor] = None
        self._ma:   MovingAverageModel = MovingAverageModel()
        self._use_rf: bool = False
        self._metrics: Dict = {}
        self._trained_prices:   List[float] = []
        self._trained_arrivals: List[float] = []
        self._trained_dates = []

    # ── Training ──────────────────────────────────────────────────────────────

    def fit(self, series: PreparedSeries) -> Dict:
        """
        Train on the series. Returns evaluation metrics.
        Uses RF when enough data, MA otherwise.
        """
        self._ma.fit(series)

        if not series.is_sufficient:
            self._use_rf = False
            self._metrics = {"mae": None, "rmse": None, "model": "MovingAverage",
                             "note": "Insufficient data for RF; using moving average"}
            self._trained_prices   = series.prices[:]
            self._trained_arrivals = series.arrivals[:]
            self._trained_dates    = series.dates[:]
            return self._metrics

        # Chronological train/test split for evaluation
        train, test = series.train_test_split()
        X_train, y_train = build_feature_matrix(train)
        X_test,  y_test  = build_feature_matrix(test)

        if len(X_train) < 5 or len(X_test) == 0:
            # Too few samples for RF after feature windowing; fall back
            self._use_rf = False
            self._metrics = self._ma.evaluate(train, test)
            self._metrics["model"] = "MovingAverage (fallback)"
            self._trained_prices   = series.prices[:]
            self._trained_arrivals = series.arrivals[:]
            self._trained_dates    = series.dates[:]
            return self._metrics

        # Train RF on ALL data (train split only for evaluation)
        rf_eval = RandomForestRegressor(**RF_PARAMS)
        rf_eval.fit(X_train, y_train)
        preds = rf_eval.predict(X_test).tolist()
        mae_val  = _mae(y_test, preds)
        rmse_val = _rmse(y_test, preds)

        # Retrain on ALL data for production predictions
        X_all, y_all = build_feature_matrix(series)
        self._rf = RandomForestRegressor(**RF_PARAMS)
        self._rf.fit(X_all, y_all)
        self._use_rf = True

        self._metrics = {
            "mae":   round(mae_val, 2),
            "rmse":  round(rmse_val, 2),
            "model": "RandomForestRegressor",
            "n_train": len(X_train),
            "n_test":  len(X_test),
        }
        self._trained_prices   = series.prices[:]
        self._trained_arrivals = series.arrivals[:]
        self._trained_dates    = series.dates[:]
        return self._metrics

    # ── Prediction ────────────────────────────────────────────────────────────

    def predict(self, horizons: List[int]) -> Dict[int, float]:
        """
        Predict modal price at each horizon (days ahead).
        Uses iterative one-step-ahead prediction — each prediction
        is appended to the history before predicting the next step.
        """
        if self._use_rf and self._rf is not None:
            return self._predict_rf(horizons)
        return self._predict_ma(horizons)

    def _predict_ma(self, horizons: List[int]) -> Dict[int, float]:
        """MA iterative prediction."""
        out = {}
        for h in horizons:
            out[h] = self._ma.predict_one(h)
        return out

    def _predict_rf(self, horizons: List[int]) -> Dict[int, float]:
        """RF iterative one-step prediction."""
        from datetime import timedelta
        prices   = self._trained_prices[:]
        arrivals = self._trained_arrivals[:]
        dates    = list(self._trained_dates)
        out: Dict[int, float] = {}
        max_horizon = max(horizons)

        for step in range(1, max_horizon + 1):
            feats = _build_features_for_prediction(prices, arrivals, dates)
            pred = float(self._rf.predict([feats])[0])
            prices.append(pred)
            arrivals.append(arrivals[-1])  # carry forward last arrival
            dates.append(dates[-1] + timedelta(days=1))
            if step in horizons:
                out[step] = round(pred, 2)

        return out

    @property
    def metrics(self) -> Dict:
        return self._metrics

    @property
    def model_name(self) -> str:
        return "RandomForestRegressor" if self._use_rf else "MovingAverage"
