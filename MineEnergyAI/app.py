"""
app.py
--------
Application entry point for MineEnergy AI.

Creates the Flask app via an application factory, registers extensions
(SQLAlchemy, Flask-Login), registers all blueprints, and seeds the
database with demo data on first run.

Run with:
    python app.py
"""

import os
from flask import Flask, render_template
from flask_login import current_user

from config import config_by_name
from extensions import db, login_manager


def create_app(env=None):
    """Application factory: builds and configures the Flask app instance."""
    env = env or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name.get(env, config_by_name["development"]))

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.machines import machines_bp
    from routes.energy import energy_bp
    from routes.alerts import alerts_bp
    from routes.predictions import predictions_bp
    from routes.reports import reports_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(machines_bp)
    app.register_blueprint(energy_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    # Jinja helper for number formatting
    from utils.helpers import format_number
    app.jinja_env.filters["fmt"] = format_number

    # Make current year available to all templates (footer)
    @app.context_processor
    def inject_globals():
        from datetime import date
        return {"current_year": date.today().year}

    # Friendly error pages
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    return app


# Flask-Login user loader must be registered once, outside the factory body
from models import User  # noqa: E402


@login_manager.user_loader
def load_user(user_id):
    """Reload a user object from the session-stored user id."""
    return db.session.get(User, int(user_id))


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Auto-seed demo data on first run if the users table is empty
        if User.query.count() == 0:
            from utils.seed_data import seed_database
            seed_database()

    app.run(debug=True, host="0.0.0.0", port=5000)
