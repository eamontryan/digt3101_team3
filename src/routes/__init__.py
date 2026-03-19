from functools import wraps
from flask import abort, session
from flask_login import current_user


def get_active_role():
    """Return the effective role for the current user.
    Dev users can switch between Admin, LeasingAgent, and Tenant via session."""
    if current_user.is_authenticated and current_user.role == 'Dev':
        return session.get('dev_active_role', 'Admin')
    return current_user.role


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            active = get_active_role()
            if active not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator
