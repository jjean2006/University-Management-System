import os
import sys

_venv_site = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venv", "lib", "python3.12", "site-packages"))
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)

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

# Pre-configured Institutional Demo Credentials
DEMO_CREDENTIALS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": ROLE_ADMIN,
        "user_id": 1,
        "entity_id": None,
        "display_name": "System Administrator",
    },
    "faculty": {
        "username": "faculty",
        "alt_username": "EMP1001",
        "password": "faculty123",
        "alt_password": "password",
        "role": ROLE_FACULTY,
        "user_id": 2,
        "entity_id": 1,
        "display_name": "Dr. Ramesh Kumar",
    },
    "student": {
        "username": "student",
        "alt_username": "25BAI0077",
        "password": "student123",
        "alt_password": "password",
        "role": ROLE_STUDENT,
        "user_id": 3,
        "entity_id": 1,
        "display_name": "Jacob Jean",
    },
    "accounts": {
        "username": "accounts",
        "password": "accounts123",
        "role": ROLE_ACCOUNTS,
        "user_id": 4,
        "entity_id": None,
        "display_name": "University Bursar",
    },
    "warden": {
        "username": "warden",
        "password": "warden123",
        "role": ROLE_WARDEN,
        "user_id": 5,
        "entity_id": None,
        "display_name": "Chief Hostel Warden",
    },
}


def authenticate_user(username, password):
    """Authenticates credentials against demo credentials and database records.

    Args:
        username: Provided username or entity identifier (EMP code / Reg No).
        password: Plaintext password string.

    Returns:
        dict containing user attributes on success, or None if authentication fails.
    """
    if not username or not password:
        return None
    if not isinstance(username, str) or not isinstance(password, str):
        return None

    clean_user = username.strip()
    clean_pass = password.strip()

    if not clean_user or not clean_pass:
        return None

    # Length guard to protect from buffer / memory overflow attempts
    if len(clean_user) > 255 or len(clean_pass) > 255:
        return None

    # 1. Check pre-configured demo credentials
    for cred in DEMO_CREDENTIALS.values():
        # Match primary username
        if clean_user.lower() == cred["username"].lower():
            if clean_pass == cred["password"]:
                return {
                    "user_id": cred["user_id"],
                    "username": cred["username"],
                    "role": cred["role"],
                    "entity_id": cred.get("entity_id"),
                    "display_name": cred.get("display_name"),
                }
            return None

        # Match alternative identifier (e.g. EMP1001 or 25BAI0077)
        alt_user = cred.get("alt_username")
        if alt_user and clean_user.upper() == alt_user.upper():
            valid_passwords = {cred["password"]}
            if cred.get("alt_password"):
                valid_passwords.add(cred["alt_password"])
            if clean_pass in valid_passwords:
                return {
                    "user_id": cred["user_id"],
                    "username": alt_user,
                    "role": cred["role"],
                    "entity_id": cred.get("entity_id"),
                    "display_name": cred.get("display_name"),
                }
            return None

    # 2. Dynamic Database Entity Credential Resolution
    # Check FACULTY table by employee_code
    try:
        faculty_rows = execute_query(
            "SELECT faculty_id, employee_code, first_name, last_name, email "
            "FROM FACULTY WHERE UPPER(employee_code) = UPPER(%s);",
            (clean_user,),
            fetch_all=True,
        )
        if faculty_rows:
            # Default password for seeded faculty is 'password' or 'faculty123'
            if clean_pass in ("password", "faculty123"):
                fac = faculty_rows[0]
                fac_id = int(fac.get("faculty_id") or fac.get("FACULTY_ID"))
                fname = fac.get("first_name") or fac.get("FIRST_NAME") or ""
                lname = fac.get("last_name") or fac.get("LAST_NAME") or ""
                code = fac.get("employee_code") or fac.get("EMPLOYEE_CODE") or clean_user
                return {
                    "user_id": 1000 + fac_id,
                    "username": code,
                    "role": ROLE_FACULTY,
                    "entity_id": fac_id,
                    "display_name": f"{fname} {lname}".strip() or "Faculty Member",
                }
            return None
    except Exception:
        pass

    # Check STUDENT table by reg_no
    try:
        student_rows = execute_query(
            "SELECT student_id, reg_no, first_name, last_name, email "
            "FROM STUDENT WHERE UPPER(reg_no) = UPPER(%s);",
            (clean_user,),
            fetch_all=True,
        )
        if student_rows:
            # Default password for seeded students is 'password' or 'student123'
            if clean_pass in ("password", "student123"):
                stu = student_rows[0]
                stu_id = int(stu.get("student_id") or stu.get("STUDENT_ID"))
                fname = stu.get("first_name") or stu.get("FIRST_NAME") or ""
                lname = stu.get("last_name") or stu.get("LAST_NAME") or ""
                reg = stu.get("reg_no") or stu.get("REG_NO") or clean_user
                return {
                    "user_id": 2000 + stu_id,
                    "username": reg,
                    "role": ROLE_STUDENT,
                    "entity_id": stu_id,
                    "display_name": f"{fname} {lname}".strip() or "Student",
                }
            return None
    except Exception:
        pass

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
