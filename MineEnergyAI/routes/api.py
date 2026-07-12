"""
routes/api.py
----------------
Lightweight JSON API blueprint used by the dashboard's JavaScript to
refresh "live" statistics and charts without a full page reload.
"""

from flask import Blueprint, jsonify
from flask_login import login_required

from services.dashboard_service import get_kpis, get_weekly_trend

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/live-stats")
@login_required
def live_stats():
    """Return current KPI numbers as JSON, used for the animated live-update effect."""
    kpis = get_kpis()
    # dates aren't JSON serialisable by default
    kpis["reference_date"] = kpis["reference_date"].strftime("%d %b %Y")
    return jsonify(kpis)


@api_bp.route("/weekly-trend")
@login_required
def weekly_trend():
    """Return the last 7 days of energy trend data as JSON."""
    return jsonify(get_weekly_trend())
