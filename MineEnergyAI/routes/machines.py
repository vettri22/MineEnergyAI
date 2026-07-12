"""
routes/machines.py
---------------------
Machine Management blueprint: list (with search + pagination), add, edit,
delete machines.
"""

from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from extensions import db
from models import Machine
from config import Config

machines_bp = Blueprint("machines", __name__, url_prefix="/machines")

MACHINE_TYPES = ["Crusher", "Conveyor", "Excavator", "Pump", "Drill", "Processing Plant"]
STATUSES = ["Active", "Idle", "Maintenance", "Offline"]


@machines_bp.route("/")
@login_required
def index():
    """List all machines with search and pagination support."""
    search = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Machine.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Machine.name.ilike(like),
                Machine.machine_code.ilike(like),
                Machine.location.ilike(like),
            )
        )
    if status_filter:
        query = query.filter(Machine.status == status_filter)

    pagination = query.order_by(Machine.id).paginate(
        page=page, per_page=Config.MACHINES_PER_PAGE, error_out=False
    )

    return render_template(
        "machines.html",
        machines=pagination.items,
        pagination=pagination,
        search=search,
        status_filter=status_filter,
        machine_types=MACHINE_TYPES,
        statuses=STATUSES,
    )


@machines_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Render the add-machine form and handle creation."""
    if request.method == "POST":
        try:
            machine = Machine(
                machine_code=request.form["machine_code"].strip().upper(),
                name=request.form["name"].strip(),
                machine_type=request.form["machine_type"],
                location=request.form["location"].strip(),
                status=request.form["status"],
                installation_date=datetime.strptime(
                    request.form["installation_date"], "%Y-%m-%d"
                ).date(),
                rated_power_kw=float(request.form.get("rated_power_kw") or 100.0),
            )
            db.session.add(machine)
            db.session.commit()
            flash(f"Machine '{machine.name}' added successfully.", "success")
            return redirect(url_for("machines.index"))
        except Exception as exc:
            db.session.rollback()
            flash(f"Could not add machine: {exc}", "danger")

    return render_template(
        "machine_form.html", machine=None, machine_types=MACHINE_TYPES, statuses=STATUSES
    )


@machines_bp.route("/edit/<int:machine_id>", methods=["GET", "POST"])
@login_required
def edit(machine_id):
    """Render the edit-machine form and handle updates."""
    machine = Machine.query.get_or_404(machine_id)

    if request.method == "POST":
        try:
            machine.machine_code = request.form["machine_code"].strip().upper()
            machine.name = request.form["name"].strip()
            machine.machine_type = request.form["machine_type"]
            machine.location = request.form["location"].strip()
            machine.status = request.form["status"]
            machine.installation_date = datetime.strptime(
                request.form["installation_date"], "%Y-%m-%d"
            ).date()
            machine.rated_power_kw = float(request.form.get("rated_power_kw") or 100.0)
            db.session.commit()
            flash(f"Machine '{machine.name}' updated successfully.", "success")
            return redirect(url_for("machines.index"))
        except Exception as exc:
            db.session.rollback()
            flash(f"Could not update machine: {exc}", "danger")

    return render_template(
        "machine_form.html", machine=machine, machine_types=MACHINE_TYPES, statuses=STATUSES
    )


@machines_bp.route("/delete/<int:machine_id>", methods=["POST"])
@login_required
def delete(machine_id):
    """Delete a machine and all its related records/alerts/predictions."""
    machine = Machine.query.get_or_404(machine_id)
    name = machine.name
    db.session.delete(machine)
    db.session.commit()
    flash(f"Machine '{name}' deleted.", "info")
    return redirect(url_for("machines.index"))
