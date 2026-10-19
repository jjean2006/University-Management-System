import os
import sys

_venv_site = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "venv", "lib", "python3.12", "site-packages")
)
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)

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

from app.auth import ROLE_ADMIN, role_required
from app.db import execute_query
from app.routes.common import COMMON_STYLES

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ADMIN_DASHBOARD_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Admin Dashboard — University Management System</title>
  <link rel="stylesheet" href="/static/css/base.css">
  <style>{COMMON_STYLES}</style>
</head>
<body>
  <header>
    <div>
      <h1>Academic Administration Dashboard</h1>
      <div class="user-meta">Role: Administrator | System Governance & Institutional Oversight</div>
    </div>
    <div>
      <a href="/logout" class="logout-link">Sign Out</a>
    </div>
  </header>

  <div class="card">
    <h2>Academic Departments</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>ID</th><th>Code</th><th>Department Name</th><th>Budget</th></tr></thead>
        <tbody>
          {{% for d in depts %}}
          <tr>
            <td class="mono">{{{{ d.dept_id }}}}</td>
            <td class="mono">{{{{ d.dept_code }}}}</td>
            <td>{{{{ d.dept_name }}}}</td>
            <td class="mono">₹{{{{ d.budget }}}}</td>
          </tr>
          {{% else %}}
          <tr><td colspan="4">No departments found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Degree Programmes</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>ID</th><th>Code</th><th>Programme Name</th><th>Department ID</th></tr></thead>
        <tbody>
          {{% for p in progs %}}
          <tr>
            <td class="mono">{{{{ p.programme_id }}}}</td>
            <td class="mono">{{{{ p.programme_code }}}}</td>
            <td>{{{{ p.programme_name }}}}</td>
            <td class="mono">{{{{ p.dept_id }}}}</td>
          </tr>
          {{% else %}}
          <tr><td colspan="4">No programmes found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Faculty Directory</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Code</th><th>Name</th><th>Email</th><th>Designation</th></tr></thead>
        <tbody>
          {{% for f in faculty %}}
          <tr>
            <td class="mono">{{{{ f.employee_code }}}}</td>
            <td>{{{{ f.first_name }}}} {{{{ f.last_name }}}}</td>
            <td class="mono">{{{{ f.email }}}}</td>
            <td>{{{{ f.designation }}}}</td>
          </tr>
          {{% else %}}
          <tr><td colspan="4">No faculty members found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Student Directory</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Reg No</th><th>Name</th><th>Programme</th><th>Department</th><th>CGPA</th></tr></thead>
        <tbody>
          {{% for s in students %}}
          <tr>
            <td class="mono">{{{{ s.reg_no }}}}</td>
            <td>{{{{ s.student_name }}}}</td>
            <td>{{{{ s.programme_name }}}}</td>
            <td>{{{{ s.dept_name }}}}</td>
            <td class="mono">{{{{ s.cgpa }}}}</td>
          </tr>
          {{% else %}}
          <tr><td colspan="5">No students found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Course Waitlist Management Overview</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Course Code</th><th>Course Title</th><th>Department</th><th>Capacity</th><th>Available Seats</th><th>Enrolled</th><th>Waitlisted</th></tr></thead>
        <tbody>
          {{% for w in waitlists %}}
          <tr>
            <td class="mono">{{{{ w.course_code }}}}</td>
            <td>{{{{ w.course_title }}}}</td>
            <td class="mono">{{{{ w.dept_code }}}}</td>
            <td class="mono">{{{{ w.capacity }}}}</td>
            <td class="mono">{{{{ w.available_seats }}}}</td>
            <td class="mono">{{{{ w.enrolled_students }}}}</td>
            <td class="mono"><span class="badge {{{{ 'badge-warning' if w.total_waitlisted > 0 else 'badge-info' }}}}">{{{{ w.total_waitlisted }}}}</span></td>
          </tr>
          {{% else %}}
          <tr><td colspan="7">No course waitlist records found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""


@admin_bp.route("/dashboard", methods=["GET"])
@role_required(ROLE_ADMIN)
def admin_dashboard():
    """Administrator Dashboard: queries departments, programmes, faculty, student directory, courses, waitlists, and users."""
    depts, progs, faculty, students, waitlists, courses, rooms, all_users = [], [], [], [], [], [], [], []
    try:
        depts = execute_query("SELECT * FROM DEPARTMENT ORDER BY dept_id;") or []
    except Exception:
        pass
    try:
        progs = execute_query("SELECT * FROM PROGRAMME ORDER BY programme_id;") or []
    except Exception:
        pass
    try:
        faculty = execute_query("SELECT * FROM FACULTY ORDER BY faculty_id;") or []
    except Exception:
        pass
    try:
        students = execute_query("SELECT * FROM v_admin_student_directory ORDER BY student_id;") or []
    except Exception:
        pass
    try:
        waitlists = execute_query("SELECT * FROM v_admin_course_waitlist ORDER BY course_code;") or []
    except Exception:
        pass
    try:
        courses = execute_query(
            "SELECT c.*, d.dept_code, d.dept_name, p.course_code AS prereq_code "
            "FROM COURSE c "
            "JOIN DEPARTMENT d ON c.dept_id = d.dept_id "
            "LEFT JOIN COURSE p ON c.prereq_course_id = p.course_id "
            "ORDER BY c.course_code;"
        ) or []
    except Exception:
        pass
    try:
        rooms = execute_query(
            "SELECT hr.room_id, hr.room_number, hb.block_name "
            "FROM HOSTEL_ROOM hr "
            "JOIN HOSTEL_BLOCK hb ON hr.block_id = hb.block_id "
            "ORDER BY hb.block_name, hr.room_number;"
        ) or []
    except Exception:
        pass
    try:
        all_users = execute_query("SELECT * FROM USER_ACCOUNT ORDER BY user_id DESC;") or []
    except Exception:
        pass

    try:
        return render_template(
            "admin/dashboard.html",
            depts=depts,
            progs=progs,
            faculty=faculty,
            students=students,
            waitlists=waitlists,
            courses=courses,
            rooms=rooms,
            all_users=all_users,
        ), 200
    except TemplateNotFound:
        return render_template_string(
            ADMIN_DASHBOARD_HTML,
            depts=depts,
            progs=progs,
            faculty=faculty,
            students=students,
            waitlists=waitlists,
            courses=courses,
            rooms=rooms,
            all_users=all_users,
        ), 200


@admin_bp.route("/courses/add", methods=["POST"])
@role_required(ROLE_ADMIN)
def admin_add_course():
    """Create a new course in the COURSE table."""
    course_code = (request.form.get("course_code") or "").strip().upper()
    course_title = (request.form.get("course_title") or "").strip()
    raw_credits = request.form.get("credits")
    raw_capacity = request.form.get("capacity")
    raw_dept_id = request.form.get("dept_id")
    raw_prereq_id = request.form.get("prereq_course_id")

    if not course_code or not course_title:
        flash("Course code and title are required.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    try:
        credits = int(raw_credits)
        capacity = int(raw_capacity)
        dept_id = int(raw_dept_id)
        prereq_id = int(raw_prereq_id) if raw_prereq_id and raw_prereq_id != "None" else None
    except (ValueError, TypeError):
        flash("Invalid numeric value for credits, capacity, or department.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    try:
        execute_query(
            "INSERT INTO COURSE (course_code, course_title, credits, capacity, available_seats, dept_id, prereq_course_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s);",
            (course_code, course_title, credits, capacity, capacity, dept_id, prereq_id),
            commit=True,
        )
        flash(f"Course {course_code} ({course_title}) created successfully.", "success")
    except Exception as e:
        flash(f"Failed to create course {course_code}: {str(e)}", "danger")

    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/users/add", methods=["POST"])
@role_required(ROLE_ADMIN)
def admin_add_user():
    """Add a user of any role. If an entity table exists (STUDENT or FACULTY), inserts into that table with all required attributes, then creates the login user in USER_ACCOUNT."""
    role = (request.form.get("role") or "").strip().lower()
    password = (
        request.form.get("password")
        or request.form.get("password_fac")
        or request.form.get("password_staff")
        or ""
    ).strip()

    if not role or not password:
        flash("Role and password are required.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    if role == "student":
        reg_no = (request.form.get("reg_no") or "").strip().upper()
        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        email = (request.form.get("email") or "").strip()
        dob = request.form.get("dob")
        gender = (request.form.get("gender") or "M").strip().upper()
        raw_cgpa = request.form.get("cgpa") or "0.00"
        raw_prog_id = request.form.get("programme_id")
        raw_advisor_id = request.form.get("advisor_id")
        raw_room_id = request.form.get("room_id")

        if not reg_no or not first_name or not last_name or not email or not dob or not raw_prog_id:
            flash("All required student attributes (Reg No, First Name, Last Name, Email, DOB, Programme) must be provided.", "danger")
            return redirect(url_for("admin.admin_dashboard"))

        try:
            cgpa = float(raw_cgpa)
            prog_id = int(raw_prog_id)
            advisor_id = int(raw_advisor_id) if raw_advisor_id and raw_advisor_id != "None" else None
            room_id = int(raw_room_id) if raw_room_id and raw_room_id != "None" else None
        except (ValueError, TypeError):
            flash("Invalid numeric value for CGPA, programme, advisor, or room.", "danger")
            return redirect(url_for("admin.admin_dashboard"))

        try:
            # 1. Insert into STUDENT table
            execute_query(
                "INSERT INTO STUDENT (reg_no, first_name, last_name, email, dob, gender, cgpa, programme_id, advisor_id, room_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                (reg_no, first_name, last_name, email, dob, gender, cgpa, prog_id, advisor_id, room_id),
                commit=True,
            )
            # Retrieve newly inserted student_id
            stu_row = execute_query("SELECT student_id FROM STUDENT WHERE reg_no = %s;", (reg_no,), fetch_one=True)
            stu_id = stu_row.get("student_id") if stu_row else None

            # 2. Insert into USER_ACCOUNT
            display_name = f"{first_name} {last_name}".strip()
            execute_query(
                "INSERT INTO USER_ACCOUNT (username, password_hash, role, entity_id, display_name, email) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash), role = VALUES(role), entity_id = VALUES(entity_id), display_name = VALUES(display_name);",
                (reg_no, password, "student", stu_id, display_name, email),
                commit=True,
            )
            flash(f"Student {display_name} ({reg_no}) successfully added to database and login account created.", "success")
        except Exception as e:
            flash(f"Failed to add student: {str(e)}", "danger")

    elif role == "faculty":
        employee_code = (request.form.get("employee_code") or "").strip().upper()
        first_name = (request.form.get("first_name_fac") or request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name_fac") or request.form.get("last_name") or "").strip()
        email = (request.form.get("email_fac") or request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        designation = (request.form.get("designation") or "Professor").strip()
        raw_dept_id = request.form.get("dept_id")

        if not employee_code or not first_name or not last_name or not email or not phone or not raw_dept_id:
            flash("All required faculty attributes (Employee Code, Name, Email, Phone, Department) must be provided.", "danger")
            return redirect(url_for("admin.admin_dashboard"))

        try:
            dept_id = int(raw_dept_id)
        except (ValueError, TypeError):
            flash("Invalid department selection.", "danger")
            return redirect(url_for("admin.admin_dashboard"))

        try:
            # 1. Insert into FACULTY table
            execute_query(
                "INSERT INTO FACULTY (employee_code, first_name, last_name, email, phone, designation, dept_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s);",
                (employee_code, first_name, last_name, email, phone, designation, dept_id),
                commit=True,
            )
            # Retrieve newly inserted faculty_id
            fac_row = execute_query("SELECT faculty_id FROM FACULTY WHERE employee_code = %s;", (employee_code,), fetch_one=True)
            fac_id = fac_row.get("faculty_id") if fac_row else None

            # 2. Insert into USER_ACCOUNT
            display_name = f"{first_name} {last_name}".strip()
            execute_query(
                "INSERT INTO USER_ACCOUNT (username, password_hash, role, entity_id, display_name, email) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash), role = VALUES(role), entity_id = VALUES(entity_id), display_name = VALUES(display_name);",
                (employee_code, password, "faculty", fac_id, display_name, email),
                commit=True,
            )
            flash(f"Faculty {display_name} ({employee_code}) successfully added to database and login account created.", "success")
        except Exception as e:
            flash(f"Failed to add faculty: {str(e)}", "danger")

    elif role in ("admin", "accounts", "warden"):
        username = (request.form.get("username") or "").strip()
        display_name = (request.form.get("display_name") or username).strip()
        email = (request.form.get("email_staff") or request.form.get("email") or f"{username}@vit.ac.in").strip()

        if not username:
            flash("Username is required.", "danger")
            return redirect(url_for("admin.admin_dashboard"))

        try:
            execute_query(
                "INSERT INTO USER_ACCOUNT (username, password_hash, role, entity_id, display_name, email) "
                "VALUES (%s, %s, %s, NULL, %s, %s) "
                "ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash), role = VALUES(role), display_name = VALUES(display_name), email = VALUES(email);",
                (username, password, role, display_name, email),
                commit=True,
            )
            flash(f"{role.capitalize()} user account '{username}' created successfully.", "success")
        except Exception as e:
            flash(f"Failed to create user account: {str(e)}", "danger")

    else:
        flash(f"Unsupported role: {role}", "danger")

    return redirect(url_for("admin.admin_dashboard"))


