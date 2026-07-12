"""
services/dashboard_service.py
--------------------------------
Aggregation helpers that compute the KPIs and chart datasets shown on the
main dashboard: today's energy, monthly energy, alerts count, efficiency
average, top consumers, carbon emissions, electricity cost, weekly/monthly
trend data, and machine comparison data.
"""

from datetime import date, timedelta
from sqlalchemy import func

from extensions import db
from models import Machine, EnergyRecord, Alert
from config import Config


def get_kpis():
    """Return the headline KPI numbers shown at the top of the dashboard."""
    today = date.today()
    # Use the most recent date with data as "today" for demo purposes
    latest_date_row = db.session.query(func.max(EnergyRecord.date)).scalar()
    ref_date = latest_date_row or today

    today_energy = (
        db.session.query(func.sum(EnergyRecord.energy_kwh))
        .filter(EnergyRecord.date == ref_date)
        .scalar()
    ) or 0.0

    month_start = ref_date.replace(day=1)
    monthly_energy = (
        db.session.query(func.sum(EnergyRecord.energy_kwh))
        .filter(EnergyRecord.date >= month_start, EnergyRecord.date <= ref_date)
        .scalar()
    ) or 0.0

    total_machines = Machine.query.count()
    open_alerts = Alert.query.filter_by(status="Open").count()

    avg_efficiency = (
        db.session.query(func.avg(EnergyRecord.efficiency_score))
        .filter(EnergyRecord.date == ref_date)
        .scalar()
    ) or 0.0

    carbon_emission_kg = today_energy * Config.CARBON_EMISSION_FACTOR
    electricity_cost = today_energy * Config.ELECTRICITY_COST_PER_KWH

    return {
        "reference_date": ref_date,
        "today_energy": round(today_energy, 1),
        "monthly_energy": round(monthly_energy, 1),
        "total_machines": total_machines,
        "open_alerts": open_alerts,
        "avg_efficiency": round(avg_efficiency, 1),
        "carbon_emission_kg": round(carbon_emission_kg, 1),
        "electricity_cost": round(electricity_cost, 2),
    }


def get_weekly_trend(reference_date=None):
    """Return the last 7 days of total daily energy consumption."""
    ref_date = reference_date or (db.session.query(func.max(EnergyRecord.date)).scalar() or date.today())
    start = ref_date - timedelta(days=6)

    rows = (
        db.session.query(EnergyRecord.date, func.sum(EnergyRecord.energy_kwh))
        .filter(EnergyRecord.date >= start, EnergyRecord.date <= ref_date)
        .group_by(EnergyRecord.date)
        .order_by(EnergyRecord.date)
        .all()
    )
    data_map = {r[0]: r[1] for r in rows}

    labels, values = [], []
    for i in range(7):
        d = start + timedelta(days=i)
        labels.append(d.strftime("%a %d"))
        values.append(round(data_map.get(d, 0.0), 1))

    return {"labels": labels, "data": values}


def get_monthly_trend(reference_date=None):
    """Return daily total energy for the current month (for area/line chart)."""
    ref_date = reference_date or (db.session.query(func.max(EnergyRecord.date)).scalar() or date.today())
    month_start = ref_date.replace(day=1)

    rows = (
        db.session.query(EnergyRecord.date, func.sum(EnergyRecord.energy_kwh))
        .filter(EnergyRecord.date >= month_start, EnergyRecord.date <= ref_date)
        .group_by(EnergyRecord.date)
        .order_by(EnergyRecord.date)
        .all()
    )
    labels = [r[0].strftime("%d %b") for r in rows]
    values = [round(r[1], 1) for r in rows]
    return {"labels": labels, "data": values}


def get_machine_type_breakdown(reference_date=None):
    """Return energy consumption grouped by machine type (for pie/doughnut chart)."""
    ref_date = reference_date or (db.session.query(func.max(EnergyRecord.date)).scalar() or date.today())
    month_start = ref_date.replace(day=1)

    rows = (
        db.session.query(Machine.machine_type, func.sum(EnergyRecord.energy_kwh))
        .join(EnergyRecord, EnergyRecord.machine_id == Machine.id)
        .filter(EnergyRecord.date >= month_start, EnergyRecord.date <= ref_date)
        .group_by(Machine.machine_type)
        .all()
    )
    labels = [r[0] for r in rows]
    values = [round(r[1], 1) for r in rows]
    return {"labels": labels, "data": values}


def get_top_consumers(limit=5, reference_date=None):
    """Return the top N energy-consuming machines for the current month."""
    ref_date = reference_date or (db.session.query(func.max(EnergyRecord.date)).scalar() or date.today())
    month_start = ref_date.replace(day=1)

    rows = (
        db.session.query(Machine.name, Machine.machine_code, func.sum(EnergyRecord.energy_kwh))
        .join(EnergyRecord, EnergyRecord.machine_id == Machine.id)
        .filter(EnergyRecord.date >= month_start, EnergyRecord.date <= ref_date)
        .group_by(Machine.id)
        .order_by(func.sum(EnergyRecord.energy_kwh).desc())
        .limit(limit)
        .all()
    )
    return [{"name": r[0], "code": r[1], "energy": round(r[2], 1)} for r in rows]


def get_machine_comparison(reference_date=None):
    """Return average daily energy per machine type for comparison bar chart."""
    ref_date = reference_date or (db.session.query(func.max(EnergyRecord.date)).scalar() or date.today())
    month_start = ref_date.replace(day=1)

    rows = (
        db.session.query(Machine.machine_type, func.avg(EnergyRecord.energy_kwh))
        .join(EnergyRecord, EnergyRecord.machine_id == Machine.id)
        .filter(EnergyRecord.date >= month_start, EnergyRecord.date <= ref_date)
        .group_by(Machine.machine_type)
        .all()
    )
    labels = [r[0] for r in rows]
    values = [round(r[1], 1) for r in rows]
    return {"labels": labels, "data": values}


def get_recent_alerts(limit=6):
    """Return the most recent open alerts for the AI Insights panel."""
    return (
        Alert.query.filter_by(status="Open")
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .all()
    )


def get_machine_health_summary():
    """Return counts of machines by status for the Machine Health panel."""
    rows = (
        db.session.query(Machine.status, func.count(Machine.id))
        .group_by(Machine.status)
        .all()
    )
    return {status: count for status, count in rows}
