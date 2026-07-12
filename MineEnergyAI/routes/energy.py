"""
routes/energy.py
-------------------
Energy Entry blueprint: form for manually logging a day's energy reading
for a machine, plus a searchable/paginated history table. Every new entry
is immediately run through the AI analysis pipeline (efficiency score +
anomaly detection + recommendation + alert creation).
"""

from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models import Machine, EnergyRecord
from services.analysis_service import analyze_energy_record
from config import Config

energy_bp = Blueprint("energy", __name__, url_prefix="/energy")


@energy_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Render the energy entry form (GET) and process new submissions (POST)."""
    machines = Machine.query.order_by(Machine.name).all()

    if request.method == "POST":
        try:
            entry_date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            machine_id = int(request.form["machine_id"])

            existing = EnergyRecord.query.filter_by(machine_id=machine_id, date=entry_date).first()
            if existing:
                flash("An energy record already exists for this machine and date. "
                      "Please edit the existing record instead.", "warning")
                return redirect(url_for("energy.index"))

            record = EnergyRecord(
                machine_id=machine_id,
                date=entry_date,
                energy_kwh=float(request.form["energy_kwh"]),
                working_hours=float(request.form["working_hours"]),
                ore_processed_tons=float(request.form["ore_processed_tons"]),
                diesel_liters=float(request.form.get("diesel_liters") or 0.0),
                operator=request.form.get("operator") or current_user.full_name,
            )
            db.session.add(record)
            db.session.flush()  # assign an ID before analysis

            analysis = analyze_energy_record(record)
            db.session.commit()

            flash(
                f"Energy record saved. Efficiency score: {analysis['efficiency_score']}/100.",
                "success",
            )
            if analysis["anomaly"]["is_anomaly"]:
                flash(
                    f"⚠ AI Alert: {analysis['recommendation']['headline']} "
                    f"({analysis['anomaly']['severity']} severity)",
                    "warning",
                )
            return redirect(url_for("energy.index"))

        except Exception as exc:
            db.session.rollback()
            flash(f"Could not save energy record: {exc}", "danger")

    # History table with search/pagination
    search = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    query = EnergyRecord.query.join(Machine)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Machine.name.ilike(like), Machine.machine_code.ilike(like))
        )

    pagination = query.order_by(EnergyRecord.date.desc()).paginate(
        page=page, per_page=Config.RECORDS_PER_PAGE, error_out=False
    )

    return render_template(
        "energy.html",
        machines=machines,
        records=pagination.items,
        pagination=pagination,
        search=search,
        today=datetime.today().strftime("%Y-%m-%d"),
    )
