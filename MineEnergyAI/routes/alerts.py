"""
routes/alerts.py
-------------------
Alerts blueprint: view critical/medium/resolved alerts with priority
color coding, and mark alerts as resolved.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import Alert, Machine
from services.analysis_service import resolve_alert

alerts_bp = Blueprint("alerts", __name__, url_prefix="/alerts")


@alerts_bp.route("/")
@login_required
def index():
    """Render the alerts page, grouped by severity/status with filters."""
    severity_filter = request.args.get("severity", "")
    status_filter = request.args.get("status", "Open")

    query = Alert.query.join(Machine)
    if severity_filter:
        query = query.filter(Alert.severity == severity_filter)
    if status_filter:
        query = query.filter(Alert.status == status_filter)

    all_alerts = query.order_by(Alert.created_at.desc()).all()

    critical_count = Alert.query.filter_by(severity="Critical", status="Open").count()
    medium_count = Alert.query.filter_by(severity="Medium", status="Open").count()
    resolved_count = Alert.query.filter_by(status="Resolved").count()

    return render_template(
        "alerts.html",
        alerts=all_alerts,
        severity_filter=severity_filter,
        status_filter=status_filter,
        critical_count=critical_count,
        medium_count=medium_count,
        resolved_count=resolved_count,
    )


@alerts_bp.route("/resolve/<int:alert_id>", methods=["POST"])
@login_required
def resolve(alert_id):
    """Mark the given alert as resolved."""
    alert = resolve_alert(alert_id)
    if alert:
        flash("Alert marked as resolved.", "success")
    else:
        flash("Alert not found.", "danger")
    return redirect(url_for("alerts.index"))
