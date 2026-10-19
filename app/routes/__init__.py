"""Routes package for University Management System (UMS).

Exports all role-based blueprints:
- auth_bp: Authentication, login, logout, and session lifecycle
- admin_bp: Academic governance and administration dashboard (/admin)
- faculty_bp: Course roster and attendance tracking (/faculty)
- student_bp: Academic profile, grades, and housing portal (/student)
- accounts_bp: Fee invoicing, collections, and defaulter audits (/accounts)
- warden_bp: Hostel block capacities and bed occupancy matrix (/warden)
"""

from app.routes.accounts_routes import accounts_bp
from app.routes.admin_routes import admin_bp
from app.routes.auth_routes import auth_bp
from app.routes.faculty_routes import faculty_bp
from app.routes.student_routes import student_bp
from app.routes.warden_routes import warden_bp

__all__ = [
    "accounts_bp",
    "admin_bp",
    "auth_bp",
    "faculty_bp",
    "student_bp",
    "warden_bp",
]
