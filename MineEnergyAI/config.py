"""
config.py
----------
Central configuration for the MineEnergy AI platform.
Holds Flask, SQLAlchemy, and application-level settings.
"""

import os

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by all environments."""

    # Secret key used to sign session cookies. In production this should
    # come from an environment variable, never hard-coded.
    SECRET_KEY = os.environ.get("SECRET_KEY", "mineenergy-ai-secret-key-2026")

    # SQLite database stored inside the project root as database.db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Application constants used by the AI / analysis modules
    ENERGY_ANOMALY_THRESHOLD_PERCENT = 15   # % above rolling average triggers alert
    CRITICAL_ANOMALY_THRESHOLD_PERCENT = 25  # % above average = critical alert
    ELECTRICITY_COST_PER_KWH = 8.50          # INR per kWh (illustrative industrial tariff)
    CARBON_EMISSION_FACTOR = 0.82            # kg CO2 per kWh (India grid average, approx.)

    # Number of days of history to seed for demo purposes
    SEED_DAYS = 365
    SEED_MACHINE_COUNT = 50

    # Pagination
    MACHINES_PER_PAGE = 10
    RECORDS_PER_PAGE = 15

    # Upload / report folders
    REPORTS_FOLDER = os.path.join(BASE_DIR, "reports", "generated")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
