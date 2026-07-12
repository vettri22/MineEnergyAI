"""
routes/reports.py
--------------------
Reports blueprint: lets users generate Daily or Monthly reports in PDF or
Excel format, downloads them, and keeps a history of generated reports.
"""

from datetime import datetime, date

from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from models import Machine, EnergyRecord, Alert, Report
from config import Config
from reports.pdf_generator import generate_pdf_report
from reports.excel_generator import generate_excel_report

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _collect_report_data(report_type, target_date):
    """Gather KPI totals and per-machine rows for the given report period."""
    if report_type == "Daily":
        start, end = target_date, target_date
        period_label = target_date.strftime("%d %B %Y")
    else:  # Monthly
        start = target_date.replace(day=1)
        end = target_date
        period_label = target_date.strftime("%B %Y")

    rows_query = (
        db.session.query(
            Machine.machine_code, Machine.name, Machine.machine_type, Machine.status,
            func.sum(EnergyRecord.energy_kwh), func.sum(EnergyRecord.ore_processed_tons),
            func.avg(EnergyRecord.efficiency_score),
        )
        .join(EnergyRecord, EnergyRecord.machine_id == Machine.id)
        .filter(EnergyRecord.date >= start, EnergyRecord.date <= end)
        .group_by(Machine.id)
        .order_by(func.sum(EnergyRecord.energy_kwh).desc())
        .all()
    )

    rows = [
        {
            "machine_code": r[0], "machine_name": r[1], "machine_type": r[2],
            "status": r[3], "energy_kwh": r[4] or 0.0, "ore_processed": r[5] or 0.0,
            "efficiency_score": r[6] or 0.0,
        }
        for r in rows_query
    ]

    total_energy = sum(r["energy_kwh"] for r in rows)
    avg_efficiency = (sum(r["efficiency_score"] for r in rows) / len(rows)) if rows else 0.0
    alert_count = Alert.query.filter(
        Alert.date >= start, Alert.date <= end, Alert.status == "Open"
    ).count()

    kpis = {
        "total_energy": total_energy,
        "total_cost": total_energy * Config.ELECTRICITY_COST_PER_KWH,
        "total_carbon": total_energy * Config.CARBON_EMISSION_FACTOR,
        "avg_efficiency": avg_efficiency,
        "machine_count": len(rows),
        "alert_count": alert_count,
    }
    return kpis, rows, period_label


@reports_bp.route("/", methods=["GET"])
@login_required
def index():
    """Render the reports page with generation controls and report history."""
    history = Report.query.order_by(Report.created_at.desc()).limit(20).all()
    latest_date = db.session.query(func.max(EnergyRecord.date)).scalar() or date.today()
    return render_template("reports.html", history=history, latest_date=latest_date)


@reports_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    """Generate a PDF or Excel report for the requested period and stream it back."""
    report_type = request.form.get("report_type", "Daily")   # Daily / Monthly
    file_format = request.form.get("file_format", "PDF")     # PDF / Excel
    target_date_str = request.form.get("target_date")

    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        target_date = db.session.query(func.max(EnergyRecord.date)).scalar() or date.today()

    kpis, rows, period_label = _collect_report_data(report_type, target_date)

    if not rows:
        flash("No energy data found for the selected period.", "warning")
        return redirect(url_for("reports.index"))

    if file_format == "Excel":
        filepath = generate_excel_report(report_type, period_label, kpis, rows)
    else:
        filepath = generate_pdf_report(report_type, period_label, kpis, rows)

    report_record = Report(
        report_type=report_type,
        file_format=file_format,
        file_name=filepath.split("/")[-1],
        generated_by=current_user.full_name,
    )
    db.session.add(report_record)
    db.session.commit()

    return send_file(filepath, as_attachment=True)
