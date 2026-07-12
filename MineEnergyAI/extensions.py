"""
extensions.py
-------------
Holds shared Flask extension instances (SQLAlchemy, LoginManager) so that
they can be imported by both app.py and the models/routes packages without
creating circular import problems.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Single SQLAlchemy database instance used across the whole application
db = SQLAlchemy()

# Flask-Login manager handles session-based authentication
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access MineEnergy AI."
login_manager.login_message_category = "warning"
