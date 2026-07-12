"""
models/models.py
-----------------
SQLAlchemy ORM models for MineEnergy AI.

Tables:
    User          - system users who can log in to the dashboard
    Machine       - physical mining machines/equipment being monitored
    EnergyRecord  - daily energy consumption reading per machine
    Alert         - system generated alerts (anomalies, maintenance, etc.)
    Prediction    - AI generated future energy predictions
    Report        - metadata for generated PDF/Excel reports
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(UserMixin, db.Model):
    """Represents a login-capable user of the platform (admin/operator)."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default="Operator")  # Admin / Manager / Operator
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        """Hash and store the given plaintext password."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.username}>"


class Machine(db.Model):
    """Represents a piece of mining equipment being monitored for energy use."""

    __tablename__ = "machines"

    id = db.Column(db.Integer, primary_key=True)
    machine_code = db.Column(db.String(20), unique=True, nullable=False)  # e.g. CR-01
    name = db.Column(db.String(120), nullable=False)
    machine_type = db.Column(db.String(50), nullable=False)  # Crusher, Conveyor, etc.
    location = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default="Active")  # Active / Idle / Maintenance / Offline
    installation_date = db.Column(db.Date, nullable=False)
    rated_power_kw = db.Column(db.Float, default=100.0)  # nameplate power rating
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    energy_records = db.relationship(
        "EnergyRecord", backref="machine", lazy="dynamic", cascade="all, delete-orphan"
    )
    alerts = db.relationship(
        "Alert", backref="machine", lazy="dynamic", cascade="all, delete-orphan"
    )
    predictions = db.relationship(
        "Prediction", backref="machine", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Machine {self.machine_code} - {self.name}>"


class EnergyRecord(db.Model):
    """A single day's energy consumption entry for a machine."""

    __tablename__ = "energy_records"

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    energy_kwh = db.Column(db.Float, nullable=False)
    working_hours = db.Column(db.Float, nullable=False)
    ore_processed_tons = db.Column(db.Float, nullable=False)
    diesel_liters = db.Column(db.Float, default=0.0)
    operator = db.Column(db.String(120), nullable=False)
    efficiency_score = db.Column(db.Float, default=0.0)  # 0-100, computed by AI service
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("machine_id", "date", name="uix_machine_date"),
    )

    def __repr__(self):
        return f"<EnergyRecord machine={self.machine_id} date={self.date}>"


class Alert(db.Model):
    """System-generated alert for anomalies, overloads, or maintenance flags."""

    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    severity = db.Column(db.String(20), nullable=False)  # Critical / Medium / Low
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    percent_deviation = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="Open")  # Open / Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Alert {self.severity} machine={self.machine_id}>"


class Prediction(db.Model):
    """Stores AI-generated future energy consumption predictions."""

    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=True)
    date = db.Column(db.Date, nullable=False)
    predicted_energy_kwh = db.Column(db.Float, nullable=False)
    model_name = db.Column(db.String(50), default="LinearRegression")
    confidence = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Prediction machine={self.machine_id} date={self.date}>"


class Report(db.Model):
    """Metadata for a generated PDF/Excel report."""

    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(20), nullable=False)  # Daily / Monthly
    file_format = db.Column(db.String(10), nullable=False)  # PDF / Excel
    file_name = db.Column(db.String(255), nullable=False)
    generated_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Report {self.file_name}>"
