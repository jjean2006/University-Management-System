import os
import sys

_venv_site = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "venv", "lib", "python3.12", "site-packages"))
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)

from urllib.parse import urlsplit
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    render_template_string,
    request,
    url_for,
)
from jinja2 import TemplateNotFound

from app.auth import (
    ROLE_DASHBOARD_ROUTES,
    authenticate_user,
    get_current_user,
    is_authenticated,
    login_user,
    logout_user,
)

auth_bp = Blueprint("auth", __name__)

LOGIN_HTML_FALLBACK = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UMS Institutional Portal — Sign In</title>
  <link rel="stylesheet" href="/static/css/base.css">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: #F8F9FA;
      color: #0F172A;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px 16px;
    }
    .login-container {
      width: 100%;
      max-width: 440px;
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 6px;
      padding: 32px 28px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    .header-section {
      text-align: center;
      margin-bottom: 24px;
      border-bottom: 1px solid #E2E8F0;
      padding-bottom: 16px;
    }
    .header-section h1 {
      font-size: 20px;
      font-weight: 600;
      color: #0F172A;
      letter-spacing: -0.01em;
      margin-bottom: 4px;
    }
    .header-section p {
      font-size: 13px;
      color: #64748B;
    }
    .alert-error {
      background-color: #FEF2F2;
      border: 1px solid #FECACA;
      color: #991B1B;
      padding: 10px 12px;
      border-radius: 4px;
      font-size: 13px;
      margin-bottom: 20px;
    }
    .form-group {
      margin-bottom: 18px;
    }
    .form-group label {
      display: block;
      font-size: 12px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #334155;
      margin-bottom: 6px;
    }
    .form-control {
      width: 100%;
      padding: 9px 12px;
      font-size: 14px;
      color: #0F172A;
      background-color: #FFFFFF;
      border: 1px solid #CBD5E1;
      border-radius: 4px;
      outline: none;
      transition: border-color 140ms ease-in-out;
    }
    .form-control:focus {
      border-color: #1E293B;
    }
    .btn-primary {
      width: 100%;
      padding: 10px 16px;
      background-color: #1E293B;
      color: #FFFFFF;
      border: 1px solid #1E293B;
      border-radius: 4px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 140ms ease-in-out;
    }
    .btn-primary:hover {
      background-color: #0F172A;
    }
    .demo-credentials-section {
      margin-top: 28px;
      border-top: 1px solid #E2E8F0;
      padding-top: 20px;
    }
    .demo-credentials-section h2 {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #64748B;
      margin-bottom: 12px;
      text-align: center;
    }
    .demo-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }
    .demo-card {
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      border-radius: 4px;
      padding: 8px 12px;
      font-size: 12px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: border-color 140ms ease-in-out, background-color 140ms ease-in-out;
    }
    .demo-card:hover {
      border-color: #CBD5E1;
      background-color: #F1F5F9;
    }
    .demo-card strong {
      color: #0F172A;
    }
    .demo-card code {
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
      color: #475569;
      font-size: 11.5px;
    }
  </style>
</head>
<body>
  <div class="login-container">
    <div class="header-section">
      <h1>University Management System</h1>
      <p>Institutional Portal Sign In &mdash; Academic Year 2026</p>
    </div>

    {% if error %}
    <div class="alert-error" role="alert">
      {{ error }}
    </div>
    {% endif %}

    <form method="POST" action="/login" id="loginForm">
      {% if next_url %}
      <input type="hidden" name="next" value="{{ next_url }}">
      {% endif %}
      <div class="form-group">
        <label for="username">Username or ID</label>
        <input type="text" id="username" name="username" class="form-control" placeholder="Enter username, EMP code, or Reg No" required autofocus>
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" class="form-control" placeholder="Enter account password" required>
      </div>
      <button type="submit" class="btn-primary">Sign In to Account</button>
    </form>

  </div>
</body>
</html>
"""


def _render_login_view(error=None, next_url=None):
    """Renders login view via template if available, otherwise using institutional fallback."""
    try:
        return render_template(
            "auth/login.html",
            error=error,
            next_url=next_url,
        )
    except TemplateNotFound:
        return render_template_string(
            LOGIN_HTML_FALLBACK,
            error=error,
            next_url=next_url,
        )


@auth_bp.route("/", methods=["GET"])
def root():
    """Root route: redirects authenticated user to role dashboard; otherwise to /login."""
    if is_authenticated():
        user = get_current_user()
        role = user.get("role") if user else None
        if role in ROLE_DASHBOARD_ROUTES:
            return redirect(ROLE_DASHBOARD_ROUTES[role])
        logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login route: presents institutional sign-in form and processes credentials."""
    next_url = request.args.get("next") or request.form.get("next")

    if request.method == "GET":
        if is_authenticated():
            user = get_current_user()
            role = user.get("role") if user else None
            if role in ROLE_DASHBOARD_ROUTES:
                return redirect(ROLE_DASHBOARD_ROUTES[role])
            logout_user()
        return _render_login_view(next_url=next_url), 200

    # POST request processing
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # Also handle JSON payload if sent by an API client
    if not username and request.is_json:
        data = request.get_json(silent=True) or {}
        username = data.get("username", "")
        password = data.get("password", "")

    user = authenticate_user(username, password)

    if not user:
        error_msg = "Invalid credentials. Please verify your username and password."
        return _render_login_view(error=error_msg, next_url=next_url), 401

    login_user(user)
    flash(f"Signed in successfully as {user.get('display_name')}.", "success")

    # Safe redirect validation: ensure internal path and not login/logout
    parsed = urlsplit(next_url) if next_url else None
    if (
        next_url
        and next_url.startswith("/")
        and not next_url.startswith(("//", "/\\", "\\"))
        and not any(next_url.startswith(p) for p in ("//", "/\\", "\\", "/%5C", "/%5c"))
        and parsed
        and not parsed.netloc
        and not parsed.scheme
        and next_url not in ("/login", "/logout")
    ):
        return redirect(next_url)

    target_dashboard = ROLE_DASHBOARD_ROUTES.get(user.get("role"), "/login")
    return redirect(target_dashboard)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Logout route: clears session and redirects to /login."""
    logout_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("auth.login"))
