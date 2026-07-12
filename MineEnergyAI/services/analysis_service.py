"""
services/analysis_service.py
------------------------------
Business-logic layer that ties together the AI modules (anomaly detection,
recommendation engine, efficiency scoring) with the database. Routes call
into this service rather than talking to the AI modules directly, keeping
the Flask views thin.
"""

from datetime import datetime

from extensions import db
from models import EnergyRecord, Alert, Machine
from ai.anomaly_detection import get_rolling_average, detect_anomaly
from ai.recommendation_engine import generate_recommendation
from ai.efficiency_score import calculate_efficiency_score


def analyze_energy_record(record: EnergyRecord, create_alert=True):
    """
    Run the full AI analysis pipeline for a single EnergyRecord:
        1. Compute its efficiency score and persist it.
        2. Compare against the machine's rolling average.
        3. If abnormal, create an Alert row (unless one already exists for
           that machine/date).

    Returns a dict with the analysis outcome, useful for flashing insights
    back to the UI immediately after manual energy entry.
    """
    machine = Machine.query.get(record.machine_id)

    # 1) Efficiency score
    record.efficiency_score = calculate_efficiency_score(
        energy_kwh=record.energy_kwh,
        working_hours=record.working_hours,
        ore_processed_tons=record.ore_processed_tons,
        rated_power_kw=machine.rated_power_kw if machine else 100.0,
    )

    # 2) Anomaly detection against rolling average
    baseline = get_rolling_average(db.session, EnergyRecord, record.machine_id, record.date)
    anomaly = detect_anomaly(record.energy_kwh, baseline)

    result = {
        "efficiency_score": record.efficiency_score,
        "baseline_average": round(baseline, 2) if baseline else None,
        "anomaly": anomaly,
        "recommendation": None,
        "alert_created": False,
    }

    # 3) Generate alert + recommendation if abnormal
    if anomaly["is_anomaly"] and machine:
        recommendation = generate_recommendation(
            machine.name, machine.machine_type, anomaly["percent_deviation"], anomaly["severity"]
        )
        result["recommendation"] = recommendation

        if create_alert:
            existing = Alert.query.filter_by(machine_id=machine.id, date=record.date).first()
            if not existing:
                alert = Alert(
                    machine_id=machine.id,
                    date=record.date,
                    severity=anomaly["severity"],
                    title=recommendation["headline"],
                    message=(
                        "Possible reasons: " + "; ".join(recommendation["reasons"]) +
                        ". Recommendations: " + "; ".join(recommendation["recommendations"])
                    ),
                    percent_deviation=anomaly["percent_deviation"],
                    status="Open",
                )
                db.session.add(alert)
                result["alert_created"] = True

    return result


def resolve_alert(alert_id):
    """Mark an alert as resolved."""
    alert = Alert.query.get(alert_id)
    if alert:
        alert.status = "Resolved"
        alert.resolved_at = datetime.utcnow()
        db.session.commit()
    return alert
