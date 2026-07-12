"""
utils/helpers.py
-------------------
Small shared helper functions used across routes/templates.
"""

from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles):
    """
    Decorator restricting a view to users with one of the given roles.
    Usage: @role_required("Admin", "Manager")
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def format_number(value, decimals=1):
    """Format a number with thousands separators for display in templates."""
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return value
