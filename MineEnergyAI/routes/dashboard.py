"""
routes/dashboard.py
----------------------
Main dashboard blueprint: renders the industrial energy overview page with
KPIs, charts, AI insights, machine health, and prediction summary.
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from services.dashboard_service import (
    get_kpis, get_weekly_trend, get_monthly_trend, get_machine_type_breakdown,
    get_top_consumers, get_machine_comparison, get_recent_alerts, get_machine_health_summary,
)
from ai.prediction_engine import predict_future_energy
from models import EnergyRecord
from extensions import db
from sqlalchemy import func

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    """Render the main dashboard with all KPI cards, charts, and AI panels."""
    kpis = get_kpis()
    weekly_trend = get_weekly_trend()
    monthly_trend = get_monthly_trend()
    machine_breakdown = get_machine_type_breakdown()
    top_consumers = get_top_consumers(limit=5)
    machine_comparison = get_machine_comparison()
    recent_alerts = get_recent_alerts(limit=6)
    machine_health = get_machine_health_summary()

    # Quick 7-day forward prediction for the dashboard prediction card
    history_rows = (
        db.session.query(EnergyRecord.date, func.sum(EnergyRecord.energy_kwh))
        .group_by(EnergyRecord.date)
        .order_by(EnergyRecord.date)
        .all()
    )
    history_dates = [r[0] for r in history_rows]
    history_values = [r[1] for r in history_rows]
    prediction = predict_future_energy(history_dates, history_values, days_ahead=7)
    prediction["future_dates_fmt"] = [d.strftime("%d %b") for d in prediction["future_dates"]]

    return render_template(
        "dashboard.html",
        kpis=kpis,
        weekly_trend=weekly_trend,
        monthly_trend=monthly_trend,
        machine_breakdown=machine_breakdown,
        top_consumers=top_consumers,
        machine_comparison=machine_comparison,
        recent_alerts=recent_alerts,
        machine_health=machine_health,
        prediction=prediction,
        current_user=current_user,
    )
