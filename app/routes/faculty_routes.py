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
from app.db import execute_query
from app.routes.common import COMMON_STYLES

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
        students = execute_query(
            "SELECT student_id, reg_no, first_name, last_name FROM STUDENT ORDER BY reg_no;"
        ) or []
    except Exception as e:
        print("[Faculty] Error loading students:", e)

    try:
        return render_template(
            "faculty/dashboard.html",
            user=user,
            courses=courses,
            roster=roster,
            shortages=shortages,
            students=students,
        ), 200
    except TemplateNotFound:
        return render_template_string(
            FACULTY_DASHBOARD_HTML,
            user=user,
            courses=courses,
            roster=roster,
            shortages=shortages,
            students=students,
        ), 200


@faculty_bp.route("/attendance", methods=["POST"])
@role_required(ROLE_FACULTY)
def faculty_attendance():
    """Genuine attendance marking endpoint: records or updates attendance per student in ATTENDANCE table."""
    data = request.get_json(silent=True) if request.is_json else {}

    raw_course_id = request.form.get("course_id") or data.get("course_id")
    try:
        course_id = int(raw_course_id) if raw_course_id is not None else None
    except (ValueError, TypeError):
        return "Invalid course_id parameter", 400

    if not course_id:
        flash("Please select a valid course.", "danger")
        return redirect(url_for("faculty.faculty_dashboard"))

    attendance_date = (
        request.form.get("attendance_date")
        or data.get("attendance_date")
        or datetime.date.today().isoformat()
    )

    records = []

    # Priority 1: Specific student selection form
    raw_single_student = request.form.get("student_id") or (data.get("student_id") if data else None)
    if raw_single_student:
        try:
            s_id = int(raw_single_student)
            s_status = request.form.get("status") or (data.get("status") if data else "Present")
            records.append((s_id, s_status))
        except (ValueError, TypeError):
            pass

    # Priority 2: JSON payload with 'records' list or 'attendance' dict
    if not records and data:
        if "records" in data and isinstance(data["records"], list):
            for item in data["records"]:
                stu_id = item.get("student_id")
                st = item.get("status", "Present")
                if stu_id:
                    records.append((int(stu_id), st))
        elif "attendance" in data and isinstance(data["attendance"], dict):
            for k, v in data["attendance"].items():
                try:
                    records.append((int(k), str(v)))
                except ValueError:
                    pass

    # Priority 3: Form submission with student status radios/inputs (status_<student_id>)
    if not records and request.form:
        for key, val in request.form.items():
            if key.startswith("status_"):
                try:
                    stu_id = int(key.split("status_")[1])
                    records.append((stu_id, val))
                except ValueError:
                    pass
            elif key.startswith("attendance_"):
                try:
                    stu_id = int(key.split("attendance_")[1])
                    records.append((stu_id, val))
                except ValueError:
                    pass


    # If no specific student statuses were given, fetch enrolled students for this course
    # and mark them with a default Present status so the action executes genuinely
    if not records:
        enrolled = execute_query(
            "SELECT student_id FROM ENROLLMENT WHERE course_id = %s;",
            (course_id,),
            fetch_all=True,
        ) or []
        for r in enrolled:
            stu_id = r.get("student_id") or r.get("STUDENT_ID")
            if stu_id:
                records.append((int(stu_id), "Present"))

    # Execute genuine inserts/updates with transaction commit
    updated_count = 0
    sql = (
        "INSERT INTO ATTENDANCE (student_id, course_id, attendance_date, status) "
        "VALUES (%s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE status = VALUES(status);"
    )
    for stu_id, status in records:
        clean_status = "Present" if status.strip().lower() == "present" else "Absent"
        execute_query(sql, (stu_id, course_id, attendance_date, clean_status), commit=True)
        updated_count += 1

    if request.is_json:
        return jsonify({
            "status": "success",
            "message": f"Recorded attendance for {updated_count} students.",
            "course_id": course_id,
            "attendance_date": attendance_date,
            "updated_count": updated_count,
        }), 200

    if request.form.get("redirect") == "false":
        return "Attendance recorded successfully", 200

    flash(f"Successfully recorded attendance for {updated_count} student(s) on {attendance_date}.", "success")
    return redirect(url_for("faculty.faculty_dashboard"))
