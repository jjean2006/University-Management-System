import os
import sys

_venv_site = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "venv", "lib", "python3.12", "site-packages")
)
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)

from flask import (
    Flask,
    render_template,
    render_template_string,
)
from jinja2 import TemplateNotFound

from app.config import Config
from app.routes import (
    accounts_bp,
    admin_bp,
    auth_bp,
    faculty_bp,
    student_bp,
    warden_bp,
)

FORBIDDEN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>403 Forbidden — Institutional Access Control</title>
  <style>
    body { background: #F8F9FA; color: #0F172A; font-family: system-ui, -apple-system, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .box { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 32px; max-width: 480px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    h1 { font-size: 20px; color: #991B1B; margin-bottom: 8px; font-weight: 600; }
    p { font-size: 14px; color: #64748B; margin-bottom: 20px; line-height: 1.5; }
    a { display: inline-block; padding: 9px 16px; background: #1E293B; color: #FFFFFF; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: 500; }
    a:hover { background: #0F172A; }
  </style>
</head>
<body>
  <div class="box">
    <h1>403 &mdash; Access Forbidden</h1>
    <p>Your authenticated role does not possess authorization to access this administrative portal section.</p>
    <a href="/login">Return to Portal Home</a>
  </div>
</body>
</html>
"""

NOT_FOUND_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>404 Not Found — Institutional Portal</title>
  <style>
    body { background: #F8F9FA; color: #0F172A; font-family: system-ui, -apple-system, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .box { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 32px; max-width: 480px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    h1 { font-size: 20px; color: #0F172A; margin-bottom: 8px; font-weight: 600; }
    p { font-size: 14px; color: #64748B; margin-bottom: 20px; line-height: 1.5; }
    a { display: inline-block; padding: 9px 16px; background: #1E293B; color: #FFFFFF; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: 500; }
    a:hover { background: #0F172A; }
  </style>
</head>
<body>
  <div class="box">
    <h1>404 &mdash; Resource Not Found</h1>
    <p>The requested endpoint could not be found on this server.</p>
    <a href="/">Return to Portal Home</a>
  </div>
</body>
</html>
"""

INTERNAL_ERROR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>500 Internal Error — Institutional Portal</title>
  <style>
    body { background: #F8F9FA; color: #0F172A; font-family: system-ui, -apple-system, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .box { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 32px; max-width: 480px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    h1 { font-size: 20px; color: #991B1B; margin-bottom: 8px; font-weight: 600; }
    p { font-size: 14px; color: #64748B; margin-bottom: 20px; line-height: 1.5; }
    a { display: inline-block; padding: 9px 16px; background: #1E293B; color: #FFFFFF; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: 500; }
    a:hover { background: #0F172A; }
  </style>
</head>
<body>
  <div class="box">
    <h1>500 &mdash; Internal Server Error</h1>
    <p>An unexpected internal error occurred while processing the request. System administrators have been alerted.</p>
    <a href="/">Return to Portal Home</a>
  </div>
</body>
</html>
"""


def create_app(config_class=None):
    """Application factory for University Management System (UMS).

    Args:
        config_class: Optional configuration class; defaults to Config from app.config.

    Returns:
        Flask application instance with registered modular blueprints and error handlers.
    """
    app = Flask(__name__)

    if config_class is None:
        config_class = Config
    app.config.from_object(config_class)

    # Secret key for session cookie encryption
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = "ums-institutional-secret-key-2026"

    # Register Modular Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(faculty_bp, url_prefix="/faculty")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(accounts_bp, url_prefix="/accounts")
    app.register_blueprint(warden_bp, url_prefix="/warden")

    # Register Common Error Handlers
    @app.errorhandler(403)
    def handle_403(e):
        try:
            return render_template("errors/403.html"), 403
        except TemplateNotFound:
            return render_template_string(FORBIDDEN_HTML), 403

    @app.errorhandler(404)
    def handle_404(e):
        try:
            return render_template("errors/404.html"), 404
        except TemplateNotFound:
            return render_template_string(NOT_FOUND_HTML), 404

    @app.errorhandler(500)
    def handle_500(e):
        try:
            return render_template("errors/500.html"), 500
        except TemplateNotFound:
            return render_template_string(INTERNAL_ERROR_HTML), 500

    return app
