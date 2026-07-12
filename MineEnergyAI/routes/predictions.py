"""
routes/predictions.py
------------------------
Predictions blueprint: shows the AI-powered future energy forecast
(overall plant-wide, and per-machine) using the scikit-learn based
prediction engine.
"""

from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import func

from extensions import db
from models import Machine, EnergyRecord
from ai.prediction_engine import predict_future_energy

predictions_bp = Blueprint("predictions", __name__, url_prefix="/predictions")


@predictions_bp.route("/")
@login_required
def index():
    """Render the prediction page for the whole plant or a selected machine."""
    machines = Machine.query.order_by(Machine.name).all()
    selected_machine_id = request.args.get("machine_id", type=int)

    query = db.session.query(EnergyRecord.date, func.sum(EnergyRecord.energy_kwh))
    if selected_machine_id:
        query = query.filter(EnergyRecord.machine_id == selected_machine_id)
    history_rows = query.group_by(EnergyRecord.date).order_by(EnergyRecord.date).all()

    history_dates = [r[0] for r in history_rows]
    history_values = [round(r[1], 1) for r in history_rows]

    prediction = predict_future_energy(history_dates, history_values, days_ahead=7)

    # Combine last 30 days of history with the forecast for the chart
    chart_labels = [d.strftime("%d %b") for d in history_dates[-30:]] + \
                    [d.strftime("%d %b") for d in prediction["future_dates"]]
    chart_history = history_values[-30:] + [None] * len(prediction["future_dates"])
    chart_forecast = [None] * len(history_values[-30:]) + prediction["future_values"]

    selected_machine = Machine.query.get(selected_machine_id) if selected_machine_id else None

    return render_template(
        "predictions.html",
        machines=machines,
        selected_machine=selected_machine,
        prediction=prediction,
        chart_labels=chart_labels,
        chart_history=chart_history,
        chart_forecast=chart_forecast,
    )
