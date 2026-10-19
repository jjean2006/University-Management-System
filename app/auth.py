import os
import sys

_venv_site = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venv", "lib", "python3.12", "site-packages"))
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)

import hmac
from functools import wraps
from flask import abort, redirect, request, session, url_for
from app.db import execute_query

# Role Constants
ROLE_ADMIN = "admin"
ROLE_FACULTY = "faculty"
ROLE_STUDENT = "student"
ROLE_ACCOUNTS = "accounts"
ROLE_WARDEN = "warden"

ALL_ROLES = [ROLE_ADMIN, ROLE_FACULTY, ROLE_STUDENT, ROLE_ACCOUNTS, ROLE_WARDEN]

# Role Dashboard Default Routes
ROLE_DASHBOARD_ROUTES = {
    ROLE_ADMIN: "/admin/dashboard",
    ROLE_FACULTY: "/faculty/dashboard",
    ROLE_STUDENT: "/student/dashboard",
    ROLE_ACCOUNTS: "/accounts/dashboard",
    ROLE_WARDEN: "/warden/dashboard",
}


def verify_password(stored, supplied):
    """Checks a supplied password against the one stored in USER_ACCOUNT (exact match only)."""
    stored = str(stored or "")
    return bool(stored) and hmac.compare_digest(stored, supplied)


def authenticate_user(username, password):
    """Authenticates credentials against the USER_ACCOUNT table.

    Args:
        username: Username, EMP code, Reg No or email address.
        password: Plaintext password string.

    Returns:
        dict containing user attributes on success, or None if authentication fails.
    """
    if not username or not password:
        return None
    if not isinstance(username, str) or not isinstance(password, str):
        return None

    clean_user = username.strip()

    if not clean_user:
        return None

    # Length guard to protect from buffer / memory overflow attempts
    if len(clean_user) > 255 or len(password) > 255:
        return None

    try:
        user_rows = execute_query(
            "SELECT user_id, username, password_hash, role, entity_id, display_name, email "
            "FROM USER_ACCOUNT WHERE UPPER(username) = UPPER(%s) OR UPPER(email) = UPPER(%s) "
            "ORDER BY UPPER(username) = UPPER(%s) DESC, user_id;",
            (clean_user, clean_user, clean_user),
            fetch_all=True,
        )
    except Exception as e:
        print("[Auth] USER_ACCOUNT lookup exception:", e)
        return None

    # An email can be shared by two accounts (e.g. 'faculty' and 'EMP1001'); accept whichever matches the password
    for u in user_rows or []:
        if verify_password(u.get("password_hash"), password):
            return {
                "user_id": int(u.get("user_id")),
                "username": u.get("username"),
                "role": u.get("role"),
                "entity_id": u.get("entity_id"),
                "display_name": u.get("display_name") or u.get("username"),
            }
    return None


def login_user(user_data):
    """Establishes active authenticated session with user identity and role.

    Args:
        user_data: dict containing user_id, username, role, entity_id, display_name.
    """
    session.clear()
    session["user_id"] = user_data.get("user_id")
    session["username"] = user_data.get("username")
    session["role"] = user_data.get("role")
    session["entity_id"] = user_data.get("entity_id")
    session["display_name"] = user_data.get("display_name")
    session["logged_in"] = True


def logout_user():
    """Terminates active session and purges all session keys."""
    session.clear()


def get_current_user():
    """Retrieves identity attributes of the currently authenticated session user.

    Returns:
        dict with user attributes if authenticated, else None.
    """
    if not is_authenticated():
        return None
    return {
        "user_id": session.get("user_id"),
        "username": session.get("username"),
        "role": session.get("role"),
        "entity_id": session.get("entity_id"),
        "display_name": session.get("display_name"),
        "logged_in": True,
    }


def is_authenticated():
    """Checks whether the current session is authenticated.

    Returns:
        bool: True if logged in, False otherwise.
    """
    return bool(session.get("logged_in") or session.get("user_id") or session.get("username"))


def login_required(view_func):
    """Route decorator enforcing authenticated session.

    Redirects unauthenticated requests to /login with the target URL in 'next'.
    """
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if not is_authenticated():
            next_url = request.path if request.method == "GET" and request.path not in ("/login", "/logout") else None
            if next_url:
                return redirect(url_for("auth.login", next=next_url))
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return decorated_view


def role_required(*allowed_roles):
    """Route decorator enforcing specific role authorizations.

    - Unauthenticated requests are redirected to /login with 'next' parameter.
    - Authenticated users lacking an authorized role are aborted with HTTP 403 Forbidden.
    """
    def decorator(view_func):
        @wraps(view_func)
        def decorated_view(*args, **kwargs):
            if not is_authenticated():
                next_url = request.path if request.method == "GET" and request.path not in ("/login", "/logout") else None
                if next_url:
                    return redirect(url_for("auth.login", next=next_url))
                return redirect(url_for("auth.login"))

            user = get_current_user()
            user_role = user.get("role") if user else None
            if user_role not in allowed_roles:
                abort(403)

            return view_func(*args, **kwargs)

        return decorated_view

    return decorator
