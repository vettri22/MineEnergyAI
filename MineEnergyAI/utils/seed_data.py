"""
utils/seed_data.py
--------------------
Generates realistic dummy data for MineEnergy AI:
    - 1 default admin user + 2 additional demo users
    - 50 machines across 6 machine types
    - 365 days of daily energy records per machine
    - Efficiency scores computed via the AI module
    - Alerts generated for detected anomalies (capped for realism)
    - A handful of AI predictions pre-computed for the dashboard

Run standalone with:  python -m utils.seed_data
or automatically via app.py on first run if the database is empty.
"""

import random
from datetime import date, timedelta

from extensions import db
from models import User, Machine, EnergyRecord, Alert, Prediction
from ai.efficiency_score import calculate_efficiency_score
from ai.anomaly_detection import detect_anomaly
from ai.recommendation_engine import generate_recommendation
from config import Config

random.seed(42)  # reproducible demo data

MACHINE_TYPES = {
    "Crusher": {"prefix": "CR", "base_power": 250, "base_ore_ratio": 3.2},
    "Conveyor": {"prefix": "CV", "base_power": 90, "base_ore_ratio": 8.5},
    "Excavator": {"prefix": "EX", "base_power": 180, "base_ore_ratio": 4.0},
    "Pump": {"prefix": "PM", "base_power": 60, "base_ore_ratio": 0.0},
    "Drill": {"prefix": "DR", "base_power": 120, "base_ore_ratio": 0.0},
    "Processing Plant": {"prefix": "PP", "base_power": 400, "base_ore_ratio": 5.5},
}

LOCATIONS = [
    "Pit A - North Bench", "Pit A - South Bench", "Pit B - East Wall",
    "Pit B - West Wall", "Ore Yard 1", "Ore Yard 2", "Crusher Station",
    "Processing Complex", "Stockpile Area", "Haul Road Junction",
]

OPERATORS = [
    "R. Kumar", "S. Sharma", "A. Verma", "P. Singh", "M. Reddy",
    "K. Nair", "V. Iyer", "D. Rao", "N. Gupta", "T. Joshi",
]


def _generate_machines(count=50):
    """Create `count` Machine records spread evenly across machine types."""
    machines = []
    type_names = list(MACHINE_TYPES.keys())
    counters = {t: 0 for t in type_names}

    for i in range(count):
        m_type = type_names[i % len(type_names)]
        counters[m_type] += 1
        info = MACHINE_TYPES[m_type]
        code = f"{info['prefix']}-{counters[m_type]:02d}"

        install_days_ago = random.randint(200, 2500)
        machine = Machine(
            machine_code=code,
            name=f"{m_type} {counters[m_type]:02d}",
            machine_type=m_type,
            location=random.choice(LOCATIONS),
            status=random.choices(
                ["Active", "Idle", "Maintenance", "Offline"],
                weights=[75, 12, 9, 4],
            )[0],
            installation_date=date.today() - timedelta(days=install_days_ago),
            rated_power_kw=info["base_power"] * random.uniform(0.85, 1.15),
        )
        machines.append(machine)

    db.session.add_all(machines)
    db.session.commit()
    return machines


def _generate_energy_history(machines, days=365):
    """
    Generate `days` days of energy history for every machine, with:
        - a mild seasonal/weekly pattern
        - random day-to-day noise
        - occasional spikes to simulate real anomalies (~4% of days)
    Efficiency scores are computed inline using the AI module.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    all_records = []
    anomaly_candidates = []  # (record, machine) pairs flagged as spikes, for alert generation

    for machine in machines:
        info = MACHINE_TYPES[machine.machine_type]
        base_energy = machine.rated_power_kw * 0.55  # avg daily kWh baseline

        # Running history buffer to compute a simple rolling baseline while seeding
        recent_energy = []

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            weekday = current_date.weekday()

            # Weekend dip (mining ops still run but lighter maintenance shifts)
            weekend_factor = 0.85 if weekday >= 5 else 1.0

            # Slow seasonal drift across the year (+/-10%)
            seasonal_factor = 1 + 0.10 * (
                (day_offset % 365) / 365.0 - 0.5
            )

            noise = random.uniform(0.92, 1.08)
            energy = base_energy * weekend_factor * seasonal_factor * noise

            # ~4% chance of an anomalous spike day
            is_spike = random.random() < 0.04
            if is_spike:
                energy *= random.uniform(1.20, 1.45)

            working_hours = round(random.uniform(14, 22) * weekend_factor, 1)
            ore_processed = round(
                energy / max(info["base_ore_ratio"], 1.5) * random.uniform(0.9, 1.1), 1
            ) if info["base_ore_ratio"] > 0 else round(random.uniform(0, 5), 1)
            diesel = round(random.uniform(0, 40), 1) if machine.machine_type in (
                "Excavator", "Drill") else 0.0

            score = calculate_efficiency_score(
                energy_kwh=energy,
                working_hours=working_hours,
                ore_processed_tons=max(ore_processed, 0.1),
                rated_power_kw=machine.rated_power_kw,
            )

            record = EnergyRecord(
                machine_id=machine.id,
                date=current_date,
                energy_kwh=round(energy, 1),
                working_hours=working_hours,
                ore_processed_tons=ore_processed,
                diesel_liters=diesel,
                operator=random.choice(OPERATORS),
                efficiency_score=score,
            )
            all_records.append(record)

            # Only evaluate anomaly for recent days (last 14) to limit alert volume
            if is_spike and day_offset >= days - 14 and len(recent_energy) >= 7:
                baseline = sum(recent_energy[-30:]) / len(recent_energy[-30:])
                anomaly = detect_anomaly(
                    energy, baseline,
                    Config.ENERGY_ANOMALY_THRESHOLD_PERCENT,
                    Config.CRITICAL_ANOMALY_THRESHOLD_PERCENT,
                )
                if anomaly["is_anomaly"]:
                    anomaly_candidates.append((record, machine, anomaly))

            recent_energy.append(energy)

    db.session.bulk_save_objects(all_records)
    db.session.commit()
    return anomaly_candidates


def _generate_alerts(anomaly_candidates):
    """Create Alert rows for the flagged anomaly candidates found while seeding."""
    alerts = []
    for record, machine, anomaly in anomaly_candidates:
        recommendation = generate_recommendation(
            machine.name, machine.machine_type, anomaly["percent_deviation"], anomaly["severity"]
        )
        status = random.choices(["Open", "Resolved"], weights=[55, 45])[0]
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
            status=status,
        )
        alerts.append(alert)

    db.session.bulk_save_objects(alerts)
    db.session.commit()


def _generate_users():
    """Create the default admin account plus a couple of demo operator accounts."""
    users = [
        User(full_name="System Administrator", username="admin",
             email="admin@mineenergy.ai", role="Admin"),
        User(full_name="Priya Sharma", username="manager",
             email="manager@mineenergy.ai", role="Manager"),
        User(full_name="Arjun Mehta", username="operator",
             email="operator@mineenergy.ai", role="Operator"),
    ]
    passwords = ["admin123", "manager123", "operator123"]
    for user, pwd in zip(users, passwords):
        user.set_password(pwd)

    db.session.add_all(users)
    db.session.commit()
    return users


def seed_database():
    """Entry point: wipes and repopulates the database with demo data."""
    print("Seeding MineEnergy AI database...")

    db.drop_all()
    db.create_all()

    print("  -> Creating users...")
    _generate_users()

    print(f"  -> Creating {Config.SEED_MACHINE_COUNT} machines...")
    machines = _generate_machines(Config.SEED_MACHINE_COUNT)

    print(f"  -> Generating {Config.SEED_DAYS} days of energy history "
          f"({Config.SEED_MACHINE_COUNT * Config.SEED_DAYS} records)... this may take a moment")
    anomaly_candidates = _generate_energy_history(machines, Config.SEED_DAYS)

    print(f"  -> Generating {len(anomaly_candidates)} alerts from detected anomalies...")
    _generate_alerts(anomaly_candidates)

    print("Database seeding complete.")
    print("Login with: admin / admin123  |  manager / manager123  |  operator / operator123")


if __name__ == "__main__":
    # Allow running as: python -m utils.seed_data
    from app import create_app

    app = create_app()
    with app.app_context():
        seed_database()
