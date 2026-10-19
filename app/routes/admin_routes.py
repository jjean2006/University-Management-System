import datetime
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
from app.db import execute_query, first_row, transaction
from app.routes.common import COMMON_STYLES
from app.validators import (
    COURSE_CODE_RE,
    EMAIL_RE,
    EMPLOYEE_CODE_RE,
    NAME_RE,
    PHONE_RE,
    REG_NO_RE,
    USERNAME_RE,
    ValidationError,
    choice,
    decimal_range,
    integer,
    iso_date,
    like_pattern,
    optional_id,
    password,
    required_text,
)

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
            "SELECT hr.room_id, hr.room_number, hb.block_name, hb.gender_type, "
            "(hr.capacity - hr.occupied_beds) AS vacant_beds "
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

    # Server-side search across the student directory view and the course catalog
    search_term = (request.args.get("q") or "").strip()[:100]
    search_students, search_courses = [], []
    if search_term:
        pattern = like_pattern(search_term)
        try:
            search_students = execute_query(
                "SELECT * FROM v_admin_student_directory "
                "WHERE reg_no LIKE %s OR student_name LIKE %s OR email LIKE %s "
                "OR programme_name LIKE %s OR dept_name LIKE %s OR faculty_advisor LIKE %s "
                "ORDER BY reg_no;",
                (pattern,) * 6,
            ) or []
            search_courses = execute_query(
                "SELECT c.course_code, c.course_title, c.credits, c.capacity, c.available_seats, d.dept_code "
                "FROM COURSE c JOIN DEPARTMENT d ON c.dept_id = d.dept_id "
                "WHERE c.course_code LIKE %s OR c.course_title LIKE %s OR d.dept_code LIKE %s "
                "ORDER BY c.course_code;",
                (pattern,) * 3,
            ) or []
        except Exception as e:
            flash(f"Search failed: {str(e)}", "danger")

    template_args = dict(
        depts=depts,
        progs=progs,
        faculty=faculty,
        students=students,
        waitlists=waitlists,
        courses=courses,
        rooms=rooms,
        all_users=all_users,
        search_term=search_term,
        search_students=search_students,
        search_courses=search_courses,
    )
    try:
        return render_template("admin/dashboard.html", **template_args), 200
    except TemplateNotFound:
        return render_template_string(ADMIN_DASHBOARD_HTML, **template_args), 200


def _course_fields(form):
    """Validates the editable course attributes shared by the add and edit forms."""
    course_title = required_text(form.get("course_title"), "Course title", 100)
    if len(course_title) < 3:
        raise ValidationError("Course title must be at least 3 characters.")
    credits = integer(form.get("credits"), "Credits", min_value=1, max_value=6)
    capacity = integer(form.get("capacity"), "Capacity", min_value=1, max_value=300)
    return course_title, credits, capacity


@admin_bp.route("/courses/add", methods=["POST"])
@role_required(ROLE_ADMIN)
def admin_add_course():
    """Create a new course in the COURSE table."""
    try:
        course_code = required_text(
            (request.form.get("course_code") or "").upper(), "Course code", 15, COURSE_CODE_RE,
            "letters followed by digits, e.g. CSE3001",
        )
        course_title, credits, capacity = _course_fields(request.form)
        dept_id = integer(request.form.get("dept_id"), "Department", min_value=1)
        prereq_id = optional_id(request.form.get("prereq_course_id"), "Prerequisite course")

        if not execute_query("SELECT 1 AS ok FROM DEPARTMENT WHERE dept_id = %s;", (dept_id,), fetch_one=True):
            raise ValidationError("Selected department does not exist.")
        if prereq_id and not execute_query("SELECT 1 AS ok FROM COURSE WHERE course_id = %s;", (prereq_id,), fetch_one=True):
            raise ValidationError("Selected prerequisite course does not exist.")
        if execute_query("SELECT 1 AS ok FROM COURSE WHERE course_code = %s;", (course_code,), fetch_one=True):
            raise ValidationError(f"Course code {course_code} already exists.")
    except ValidationError as e:
        flash(str(e), "danger")
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


@admin_bp.route("/courses/<int:course_id>/edit", methods=["POST"])
@role_required(ROLE_ADMIN)
def admin_edit_course(course_id):
    """Update a course's title, credits and capacity; available seats move with the capacity change."""
    try:
        course_title, credits, capacity = _course_fields(request.form)
        with transaction() as cur:
            cur.execute(
                "SELECT course_code, capacity, available_seats FROM COURSE WHERE course_id = %s FOR UPDATE;",
                (course_id,),
            )
            course = first_row(cur)
            if not course:
                raise ValidationError("Course not found.")
            seats_taken = int(course.get("capacity")) - int(course.get("available_seats"))
            if capacity < seats_taken:
                raise ValidationError(
                    f"Capacity cannot be reduced below the {seats_taken} seats already taken in {course.get('course_code')}."
                )
            cur.execute(
                "UPDATE COURSE SET course_title = %s, credits = %s, capacity = %s, available_seats = %s "
                "WHERE course_id = %s;",
                (course_title, credits, capacity, capacity - seats_taken, course_id),
            )
        flash(f"Course {course.get('course_code')} updated successfully.", "success")
    except ValidationError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Failed to update course: {str(e)}", "danger")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@role_required(ROLE_ADMIN)
def admin_delete_course(course_id):
    """Delete a course that has no students currently enrolled (cascades to its waitlist and history)."""
    try:
        with transaction() as cur:
            cur.execute("SELECT course_code FROM COURSE WHERE course_id = %s FOR UPDATE;", (course_id,))
            course = first_row(cur)
            if not course:
                raise ValidationError("Course not found.")
            cur.execute(
                "SELECT COUNT(*) AS active FROM ENROLLMENT WHERE course_id = %s AND completion_status = 'ENROLLED';",
                (course_id,),
            )
            active = int(first_row(cur).get("active"))
            if active:
                raise ValidationError(
                    f"{course.get('course_code')} has {active} student(s) currently enrolled and cannot be deleted."
                )
            # ON DELETE CASCADE removes ENROLLMENT/ATTENDANCE/COURSE_WAITLIST rows;
            # ON DELETE SET NULL clears prereq_course_id on dependent courses.
            cur.execute("DELETE FROM COURSE WHERE course_id = %s;", (course_id,))
        flash(f"Course {course.get('course_code')} deleted.", "success")
    except ValidationError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Failed to delete course: {str(e)}", "danger")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/students/<int:student_id>/delete", methods=["POST"])
@role_required(ROLE_ADMIN)
def admin_delete_student(student_id):
    """Delete a student, their login, and release their course seats and hostel bed."""
    try:
        with transaction() as cur:
            cur.execute("SELECT reg_no, room_id FROM STUDENT WHERE student_id = %s FOR UPDATE;", (student_id,))
            student = first_row(cur)
            if not student:
                raise ValidationError("Student not found.")

            # Release one seat in every course the student is still taking
            cur.execute(
                "UPDATE COURSE c JOIN ENROLLMENT e ON e.course_id = c.course_id "
                "SET c.available_seats = LEAST(c.capacity, c.available_seats + 1) "
                "WHERE e.student_id = %s AND e.completion_status = 'ENROLLED';",
                (student_id,),
            )
            if student.get("room_id") is not None:
                cur.execute(
                    "UPDATE HOSTEL_ROOM SET occupied_beds = GREATEST(occupied_beds - 1, 0) WHERE room_id = %s;",
                    (student.get("room_id"),),
                )
            cur.execute("DELETE FROM USER_ACCOUNT WHERE role = 'student' AND entity_id = %s;", (student_id,))
            # ON DELETE CASCADE removes ENROLLMENT, ATTENDANCE, COURSE_WAITLIST and FEE_PAYMENT rows
            cur.execute("DELETE FROM STUDENT WHERE student_id = %s;", (student_id,))
        flash(f"Student {student.get('reg_no')} and all related records were deleted.", "success")
    except ValidationError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Failed to delete student: {str(e)}", "danger")
    return redirect(url_for("admin.admin_dashboard"))


def _ensure_username_free(cur, username):
    cur.execute("SELECT 1 AS ok FROM USER_ACCOUNT WHERE UPPER(username) = UPPER(%s);", (username,))
    if first_row(cur):
        raise ValidationError(f"A login account with username '{username}' already exists.")


def _add_student(form, password):
    reg_no = required_text((form.get("reg_no") or "").upper(), "Registration number", 15, REG_NO_RE, "format like 25BCE1001")
    first_name = required_text(form.get("first_name"), "First name", 50, NAME_RE, "letters only")
    last_name = required_text(form.get("last_name"), "Last name", 50, NAME_RE, "letters only")
    email = required_text(form.get("email"), "Email", 100, EMAIL_RE, "a valid email address")
    today = datetime.date.today()
    day = min(today.day, 28)  # avoids Feb 29 when shifting years
    dob = iso_date(
        form.get("dob"), "Date of birth",
        not_after=datetime.date(today.year - 15, today.month, day),
        not_before=datetime.date(today.year - 60, today.month, day),
    )
    gender = choice((form.get("gender") or "").upper(), "Gender", ("M", "F"))
    cgpa = decimal_range(form.get("cgpa") or "0", "CGPA", "0.00", "10.00")
    prog_id = integer(form.get("programme_id"), "Programme", min_value=1)
    advisor_id = optional_id(form.get("advisor_id"), "Faculty advisor")
    room_id = optional_id(form.get("room_id"), "Hostel room")

    with transaction() as cur:
        _ensure_username_free(cur, reg_no)
        cur.execute("SELECT 1 AS ok FROM STUDENT WHERE reg_no = %s OR email = %s;", (reg_no, email))
        if first_row(cur):
            raise ValidationError(f"A student with registration number {reg_no} or email {email} already exists.")
        cur.execute("SELECT 1 AS ok FROM PROGRAMME WHERE programme_id = %s;", (prog_id,))
        if not first_row(cur):
            raise ValidationError("Selected programme does not exist.")
        if advisor_id:
            cur.execute("SELECT 1 AS ok FROM FACULTY WHERE faculty_id = %s;", (advisor_id,))
            if not first_row(cur):
                raise ValidationError("Selected faculty advisor does not exist.")
        if room_id:
            cur.execute(
                "SELECT hr.room_number, hr.capacity, hr.occupied_beds, hb.gender_type, hb.block_name "
                "FROM HOSTEL_ROOM hr JOIN HOSTEL_BLOCK hb ON hr.block_id = hb.block_id "
                "WHERE hr.room_id = %s FOR UPDATE;",
                (room_id,),
            )
            room = first_row(cur)
            if not room:
                raise ValidationError("Selected hostel room does not exist.")
            if room.get("gender_type") != gender:
                raise ValidationError(f"{room.get('block_name')} does not accept students of gender '{gender}'.")
            if int(room.get("occupied_beds")) >= int(room.get("capacity")):
                raise ValidationError(f"Room {room.get('room_number')} is full.")
            cur.execute("UPDATE HOSTEL_ROOM SET occupied_beds = occupied_beds + 1 WHERE room_id = %s;", (room_id,))

        cur.execute(
            "INSERT INTO STUDENT (reg_no, first_name, last_name, email, dob, gender, cgpa, programme_id, advisor_id, room_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
            (reg_no, first_name, last_name, email, dob.isoformat(), gender, cgpa, prog_id, advisor_id, room_id),
        )
        cur.execute("SELECT student_id FROM STUDENT WHERE reg_no = %s;", (reg_no,))
        stu_id = first_row(cur).get("student_id")
        display_name = f"{first_name} {last_name}"
        cur.execute(
            "INSERT INTO USER_ACCOUNT (username, password_hash, role, entity_id, display_name, email) "
            "VALUES (%s, %s, 'student', %s, %s, %s);",
            (reg_no, password, stu_id, display_name, email),
        )
    return f"Student {display_name} ({reg_no}) successfully added to database and login account created."


def _add_faculty(form, password):
    employee_code = required_text(
        (form.get("employee_code") or "").upper(), "Employee code", 15, EMPLOYEE_CODE_RE, "format like EMP1004"
    )
    first_name = required_text(form.get("first_name_fac") or form.get("first_name"), "First name", 50, NAME_RE, "letters only")
    last_name = required_text(form.get("last_name_fac") or form.get("last_name"), "Last name", 50, NAME_RE, "letters only")
    email = required_text(form.get("email_fac") or form.get("email"), "Email", 100, EMAIL_RE, "a valid email address")
    phone = required_text(form.get("phone"), "Phone number", 15, PHONE_RE, "10 digits")
    designation = choice(
        form.get("designation") or "Professor", "Designation",
        ("Professor", "Associate Professor", "Assistant Professor", "Senior Lecturer"),
    )
    dept_id = integer(form.get("dept_id"), "Department", min_value=1)

    with transaction() as cur:
        _ensure_username_free(cur, employee_code)
        cur.execute("SELECT 1 AS ok FROM FACULTY WHERE employee_code = %s OR email = %s;", (employee_code, email))
        if first_row(cur):
            raise ValidationError(f"A faculty member with code {employee_code} or email {email} already exists.")
        cur.execute("SELECT 1 AS ok FROM DEPARTMENT WHERE dept_id = %s;", (dept_id,))
        if not first_row(cur):
            raise ValidationError("Selected department does not exist.")
        cur.execute(
            "INSERT INTO FACULTY (employee_code, first_name, last_name, email, phone, designation, dept_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s);",
            (employee_code, first_name, last_name, email, phone, designation, dept_id),
        )
        cur.execute("SELECT faculty_id FROM FACULTY WHERE employee_code = %s;", (employee_code,))
        fac_id = first_row(cur).get("faculty_id")
        display_name = f"{first_name} {last_name}"
        cur.execute(
            "INSERT INTO USER_ACCOUNT (username, password_hash, role, entity_id, display_name, email) "
            "VALUES (%s, %s, 'faculty', %s, %s, %s);",
            (employee_code, password, fac_id, display_name, email),
        )
    return f"Faculty {display_name} ({employee_code}) successfully added to database and login account created."


def _add_staff(form, password, role):
    username = required_text(form.get("username"), "Username", 50, USERNAME_RE, "3-50 letters, digits, '_' or '.'")
    display_name = (form.get("display_name") or username).strip()[:100]
    email = required_text(
        form.get("email_staff") or form.get("email") or f"{username}@vit.ac.in", "Email", 100, EMAIL_RE, "a valid email address"
    )
    with transaction() as cur:
        _ensure_username_free(cur, username)
        cur.execute(
            "INSERT INTO USER_ACCOUNT (username, password_hash, role, entity_id, display_name, email) "
            "VALUES (%s, %s, %s, NULL, %s, %s);",
            (username, password, role, display_name, email),
        )
    return f"{role.capitalize()} user account '{username}' created successfully."


@admin_bp.route("/users/add", methods=["POST"])
@role_required(ROLE_ADMIN)
def admin_add_user():
    """Add a user of any role. Students and faculty are inserted into their entity table and
    USER_ACCOUNT in one transaction; existing accounts are never overwritten."""
    role = (request.form.get("role") or "").strip().lower()
    raw_password = (
        request.form.get("password")
        or request.form.get("password_fac")
        or request.form.get("password_staff")
        or ""
    )

    try:
        role = choice(role, "Role", ("student", "faculty", "admin", "accounts", "warden"))
        pwd = password(raw_password)
        if role == "student":
            message = _add_student(request.form, pwd)
        elif role == "faculty":
            message = _add_faculty(request.form, pwd)
        else:
            message = _add_staff(request.form, pwd, role)
        flash(message, "success")
    except ValidationError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Failed to add {role or 'user'}: {str(e)}", "danger")

    return redirect(url_for("admin.admin_dashboard"))
