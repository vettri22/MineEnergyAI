"""
ai/prediction_engine.py
--------------------------
Uses scikit-learn's Linear Regression to forecast future energy
consumption based on historical daily totals.

Approach:
    - Aggregate historical total energy per day (across all machines, or a
      single machine if machine_id is provided).
    - Fit a simple linear regression of energy vs. day-index, capturing the
      overall trend.
    - Also compute a 7-day seasonal average pattern (day-of-week effect) to
      make the forward forecast a bit more realistic than a pure straight
      line.
    - Predict the next N days (default 7) and return them.
"""

from datetime import timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


def predict_future_energy(history_dates, history_values, days_ahead=7):
    """
    Fit a linear regression model on the historical (date, value) series and
    project `days_ahead` future values.

    Args:
        history_dates: list[datetime.date] sorted ascending
        history_values: list[float] same length as history_dates
        days_ahead: number of future days to predict

    Returns:
        {
            "future_dates": [date, ...],
            "future_values": [float, ...],
            "confidence": float (R^2 score of the fit, 0-1),
            "trend": "increasing" | "decreasing" | "stable"
        }
    """
    if len(history_dates) < 7:
        # Not enough data - fall back to flat projection using the mean
        avg = float(np.mean(history_values)) if history_values else 0.0
        last_date = history_dates[-1] if history_dates else None
        future_dates = [
            (last_date + timedelta(days=i)) if last_date else None
            for i in range(1, days_ahead + 1)
        ]
        return {
            "future_dates": future_dates,
            "future_values": [round(avg, 2)] * days_ahead,
            "confidence": 0.0,
            "trend": "stable",
        }

    X = np.arange(len(history_dates)).reshape(-1, 1)
    y = np.array(history_values)

    model = LinearRegression()
    model.fit(X, y)

    y_pred_fit = model.predict(X)
    confidence = max(0.0, min(1.0, r2_score(y, y_pred_fit)))

    # Compute a day-of-week seasonal adjustment (average deviation from trend
    # for each weekday) to make the forecast slightly more realistic.
    residuals = y - y_pred_fit
    weekday_adjustment = {}
    for i, d in enumerate(history_dates):
        wd = d.weekday()
        weekday_adjustment.setdefault(wd, []).append(residuals[i])
    weekday_adjustment = {
        wd: float(np.mean(vals)) for wd, vals in weekday_adjustment.items()
    }

    last_date = history_dates[-1]
    future_X = np.arange(len(history_dates), len(history_dates) + days_ahead).reshape(-1, 1)
    base_predictions = model.predict(future_X)

    future_dates = []
    future_values = []
    for i in range(days_ahead):
        f_date = last_date + timedelta(days=i + 1)
        adj = weekday_adjustment.get(f_date.weekday(), 0.0)
        value = max(0.0, base_predictions[i] + adj)
        future_dates.append(f_date)
        future_values.append(round(float(value), 2))

    slope = model.coef_[0]
    if slope > 0.5:
        trend = "increasing"
    elif slope < -0.5:
        trend = "decreasing"
    else:
        trend = "stable"

    return {
        "future_dates": future_dates,
        "future_values": future_values,
        "confidence": round(confidence, 2),
        "trend": trend,
    }
