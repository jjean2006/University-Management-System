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
    jsonify,
    redirect,
    render_template,
    render_template_string,
    request,
    url_for,
)
from jinja2 import TemplateNotFound

from app.auth import ROLE_FACULTY, get_current_user, role_required
from app.db import execute_query, transaction
from app.routes.common import COMMON_STYLES
from app.validators import ValidationError, choice, integer, iso_date

faculty_bp = Blueprint("faculty", __name__, url_prefix="/faculty")

FACULTY_DASHBOARD_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Faculty Dashboard — University Management System</title>
  <link rel="stylesheet" href="/static/css/base.css">
  <style>{COMMON_STYLES}</style>
</head>
<body>
  <header>
    <div>
      <h1>Faculty Academic Dashboard</h1>
      <div class="user-meta">{{{{ user.display_name if user else 'Dr. Ramesh Kumar' }}}} | Employee Code: {{{{ user.username if user else 'EMP1001' }}}}</div>
    </div>
    <div>
      <a href="/logout" class="logout-link">Sign Out</a>
    </div>
  </header>

  {{% with messages = get_flashed_messages(with_categories=true) %}}
    {{% if messages %}}
      {{% for category, message in messages %}}
        <div class="alert alert-{{{{ 'error' if category == 'error' else 'success' }}}}">{{{{ message }}}}</div>
      {{% endfor %}}
    {{% endif %}}
  {{% endwith %}}

  <div class="card">
    <h2>Assigned Courses</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Course Code</th><th>Course Title</th><th>Credits</th><th>Capacity</th><th>Available Seats</th></tr></thead>
        <tbody>
          {{% for c in courses %}}
          <tr>
            <td class="mono">{{{{ c.course_code }}}}</td>
            <td>{{{{ c.course_title }}}}</td>
            <td class="mono">{{{{ c.credits }}}}</td>
            <td class="mono">{{{{ c.capacity }}}}</td>
            <td class="mono">{{{{ c.available_seats }}}}</td>
          </tr>
          {{% else %}}
          <tr><td colspan="5">No assigned courses found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Student Attendance Shortage Alerts (&lt; 75%)</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Reg No</th><th>Student Name</th><th>Course Code</th><th>Classes Conducted</th><th>Classes Attended</th><th>Attendance %</th><th>Status</th></tr></thead>
        <tbody>
          {{% for sh in shortages %}}
          <tr>
            <td class="mono">{{{{ sh.reg_no }}}}</td>
            <td>{{{{ sh.student_name }}}}</td>
            <td class="mono">{{{{ sh.course_code }}}}</td>
            <td class="mono">{{{{ sh.total_classes_conducted }}}}</td>
            <td class="mono">{{{{ sh.classes_attended }}}}</td>
            <td class="mono">{{{{ sh.attendance_percentage }}}}%</td>
            <td><span class="badge badge-danger">Shortage Warning</span></td>
          </tr>
          {{% else %}}
          <tr><td colspan="7">No students currently in attendance shortage.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Active Course Enrolled Student Roster</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Reg No</th><th>Student Name</th><th>Course Code</th><th>Course Title</th><th>Enrollment Date</th><th>Status</th></tr></thead>
        <tbody>
          {{% for r in roster %}}
          <tr>
            <td class="mono">{{{{ r.reg_no }}}}</td>
            <td>{{{{ r.student_name if r.student_name else (r.first_name ~ ' ' ~ r.last_name) }}}}</td>
            <td class="mono">{{{{ r.course_code }}}}</td>
            <td>{{{{ r.course_title }}}}</td>
            <td class="mono">{{{{ r.enrollment_date if r.enrollment_date else '2026-08-01' }}}}</td>
            <td><span class="badge badge-info">{{{{ r.completion_status }}}}</span></td>
          </tr>
          {{% else %}}
          <tr><td colspan="6">No students enrolled in courses.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Record Daily Lecture Attendance</h2>
    <form method="POST" action="/faculty/attendance">
      <div style="display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 16px;">
        <div>
          <label style="display: block; font-size: 12px; font-weight: 500; text-transform: uppercase; margin-bottom: 4px; color: #334155;">Course:</label>
          <select name="course_id" class="form-control" style="min-width: 260px;" required>
            {{% for c in courses %}}
            <option value="{{{{ c.course_id }}}}">{{{{ c.course_code }}}} &mdash; {{{{ c.course_title }}}}</option>
            {{% endfor %}}
          </select>
        </div>
        <div>
          <label style="display: block; font-size: 12px; font-weight: 500; text-transform: uppercase; margin-bottom: 4px; color: #334155;">Lecture Date:</label>
          <input type="date" name="attendance_date" class="form-control" value="2026-10-19" required>
        </div>
      </div>

      <div class="table-responsive" style="margin-bottom: 16px;">
        <table>
          <thead>
            <tr>
              <th>Reg No</th>
              <th>Student Name</th>
              <th>Attendance Status</th>
            </tr>
          </thead>
          <tbody>
            {{% for s in students %}}
            <tr>
              <td class="mono">{{{{ s.reg_no }}}}</td>
              <td>{{{{ s.first_name }}}} {{{{ s.last_name }}}}</td>
              <td>
                <label style="margin-right: 16px; cursor: pointer;">
                  <input type="radio" name="status_{{{{ s.student_id }}}}" value="Present" checked> Present
                </label>
                <label style="cursor: pointer;">
                  <input type="radio" name="status_{{{{ s.student_id }}}}" value="Absent"> Absent
                </label>
              </td>
            </tr>
            {{% endfor %}}
          </tbody>
        </table>
      </div>

      <button type="submit" class="btn btn-primary">Submit Daily Attendance</button>
    </form>
  </div>
</body>
</html>
"""


@faculty_bp.route("/dashboard", methods=["GET"])
@role_required(ROLE_FACULTY)
def faculty_dashboard():
    """Faculty Dashboard: displays assigned courses, student rosters, and attendance shortages."""
    user = get_current_user()
    courses, roster, shortages, students = [], [], [], []
    try:
        courses = execute_query("SELECT * FROM COURSE ORDER BY course_id;") or []
    except Exception as e:
        print("[Faculty] Error loading courses:", e)

    try:
        roster = execute_query("SELECT * FROM v_faculty_view ORDER BY course_code, reg_no;") or []
    except Exception as e:
        print("[Faculty] Error loading roster:", e)

    try:
        shortages = execute_query("SELECT * FROM v_faculty_attendance_shortage;") or []
    except Exception as e:
        print("[Faculty] Error loading shortages:", e)

    try:
        # Each student carries the ids of the courses they are actively enrolled in, so the
        # attendance forms only offer students who belong to the selected course.
        students = execute_query(
            "SELECT s.student_id, s.reg_no, s.first_name, s.last_name, "
            "GROUP_CONCAT(e.course_id ORDER BY e.course_id) AS course_ids "
            "FROM STUDENT s "
            "JOIN ENROLLMENT e ON e.student_id = s.student_id AND e.completion_status = 'ENROLLED' "
            "GROUP BY s.student_id, s.reg_no, s.first_name, s.last_name "
            "ORDER BY s.reg_no;"
        ) or []
    except Exception as e:
        print("[Faculty] Error loading students:", e)

    template_args = dict(
        user=user,
        courses=courses,
        roster=roster,
        shortages=shortages,
        students=students,
        today=datetime.date.today().isoformat(),
    )
    try:
        return render_template("faculty/dashboard.html", **template_args), 200
    except TemplateNotFound:
        return render_template_string(FACULTY_DASHBOARD_HTML, **template_args), 200


def _attendance_error(message):
    if request.is_json:
        return jsonify({"status": "error", "message": message}), 400
    flash(message, "danger")
    return redirect(url_for("faculty.faculty_dashboard"))


@faculty_bp.route("/attendance", methods=["POST"])
@role_required(ROLE_FACULTY)
def faculty_attendance():
    """Records or updates attendance in the ATTENDANCE table for students enrolled in the course."""
    data = (request.get_json(silent=True) or {}) if request.is_json else {}

    raw_course_id = request.form.get("course_id") or data.get("course_id")
    try:
        course_id = integer(raw_course_id, "Course", min_value=1)
        attendance_date = iso_date(
            request.form.get("attendance_date") or data.get("attendance_date") or datetime.date.today().isoformat(),
            "Lecture date",
            not_after=datetime.date.today(),
        )
    except ValidationError as e:
        return _attendance_error(str(e))

    course = execute_query("SELECT course_code FROM COURSE WHERE course_id = %s;", (course_id,), fetch_one=True)
    if not course:
        return _attendance_error(f"Course #{course_id} does not exist.")

    records = []

    # Priority 1: Specific student selection form
    raw_single_student = request.form.get("student_id") or data.get("student_id")
    if raw_single_student:
        records.append((raw_single_student, request.form.get("status") or data.get("status")))

    # Priority 2: JSON payload with 'records' list or 'attendance' dict
    if not records and data:
        if isinstance(data.get("records"), list):
            for item in data["records"]:
                if isinstance(item, dict) and item.get("student_id"):
                    records.append((item.get("student_id"), item.get("status")))
        elif isinstance(data.get("attendance"), dict):
            records.extend(data["attendance"].items())

    # Priority 3: Batch sheet radios (status_<student_id>)
    if not records and request.form:
        for key, val in request.form.items():
            for prefix in ("status_", "attendance_"):
                # suffix must be a student id ("attendance_date" is not a student field)
                if key.startswith(prefix) and key[len(prefix):].isdigit():
                    records.append((key[len(prefix):], val))

    if not records:
        return _attendance_error("No students were selected for attendance.")

    try:
        records = [
            (integer(stu_id, "Student", min_value=1), choice(str(status or ""), "Attendance status", ("Present", "Absent")))
            for stu_id, status in records
        ]
    except ValidationError as e:
        return _attendance_error(str(e))

    enrolled = {
        int(r.get("student_id"))
        for r in execute_query(
            "SELECT student_id FROM ENROLLMENT WHERE course_id = %s AND completion_status = 'ENROLLED';",
            (course_id,),
        ) or []
    }
    valid = [(sid, st) for sid, st in records if sid in enrolled]
    skipped = len(records) - len(valid)
    if not valid:
        return _attendance_error(f"None of the selected students are enrolled in {course.get('course_code')}.")

    sql = (
        "INSERT INTO ATTENDANCE (student_id, course_id, attendance_date, status) "
        "VALUES (%s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE status = VALUES(status);"
    )
    with transaction() as cur:
        for stu_id, status in valid:
            cur.execute(sql, (stu_id, course_id, attendance_date.isoformat(), status))
    updated_count = len(valid)

    if request.is_json:
        return jsonify({
            "status": "success",
            "message": f"Recorded attendance for {updated_count} students.",
            "course_id": course_id,
            "attendance_date": attendance_date.isoformat(),
            "updated_count": updated_count,
            "skipped_count": skipped,
        }), 200

    if request.form.get("redirect") == "false":
        return "Attendance recorded successfully", 200

    message = f"Successfully recorded attendance for {updated_count} student(s) in {course.get('course_code')} on {attendance_date.isoformat()}."
    if skipped:
        message += f" {skipped} student(s) skipped because they are not enrolled in this course."
    flash(message, "success")
    return redirect(url_for("faculty.faculty_dashboard"))
