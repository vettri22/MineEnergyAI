"""
ai/anomaly_detection.py
------------------------
Rule-based anomaly detection for machine energy consumption.

The approach:
    1. Compute the trailing rolling average energy consumption for a
       machine (last 30 days, excluding the day being checked).
    2. Compare today's reading against that baseline.
    3. Classify the deviation into Normal / Medium / Critical based on
       configurable percentage thresholds.

This intentionally avoids "black box" ML for anomaly flagging so that the
logic is fully explainable to mining engineers - a requirement in real
industrial software.
"""

from datetime import timedelta
from statistics import mean


def get_rolling_average(session, EnergyRecord, machine_id, current_date, window_days=30):
    """
    Return the average energy_kwh for a machine over the `window_days`
    days prior to current_date (excluding current_date itself).
    Returns None if there isn't enough history.
    """
    start_date = current_date - timedelta(days=window_days)
    records = (
        session.query(EnergyRecord)
        .filter(
            EnergyRecord.machine_id == machine_id,
            EnergyRecord.date >= start_date,
            EnergyRecord.date < current_date,
        )
        .all()
    )
    if not records:
        return None
    return mean([r.energy_kwh for r in records])


def detect_anomaly(current_energy, baseline_average, medium_threshold=15, critical_threshold=25):
    """
    Compare current_energy to baseline_average and return a dict describing
    the anomaly status.

    Returns:
        {
            "is_anomaly": bool,
            "severity": "Normal" | "Medium" | "Critical",
            "percent_deviation": float
        }
    """
    if baseline_average is None or baseline_average == 0:
        return {"is_anomaly": False, "severity": "Normal", "percent_deviation": 0.0}

    percent_deviation = ((current_energy - baseline_average) / baseline_average) * 100

    if percent_deviation >= critical_threshold:
        severity = "Critical"
        is_anomaly = True
    elif percent_deviation >= medium_threshold:
        severity = "Medium"
        is_anomaly = True
    else:
        severity = "Normal"
        is_anomaly = False

    return {
        "is_anomaly": is_anomaly,
        "severity": severity,
        "percent_deviation": round(percent_deviation, 2),
    }
