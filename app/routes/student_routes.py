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

from app.auth import ROLE_STUDENT, get_current_user, role_required
from app.db import execute_query
from app.routes.common import COMMON_STYLES

student_bp = Blueprint("student", __name__, url_prefix="/student")

STUDENT_DASHBOARD_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Student Dashboard — University Management System</title>
  <link rel="stylesheet" href="/static/css/base.css">
  <style>{COMMON_STYLES}</style>
</head>
<body>
  <header>
    <div>
      <h1>Student Academic Portal</h1>
      <div class="user-meta">Welcome, {{{{ student.first_name }}}} {{{{ student.last_name }}}} | Academic Status: Active</div>
    </div>
    <div>
      <a href="/logout" class="logout-link">Sign Out</a>
    </div>
  </header>

  <div class="card">
    <h2>Academic Profile</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 12px;">
      <div>
        <span style="font-size: 11px; font-weight: 500; text-transform: uppercase; color: #64748B;">Registration Number</span>
        <div class="mono" style="font-size: 15px; font-weight: 600; margin-top: 2px;">{{{{ student.reg_no }}}}</div>
      </div>
      <div>
        <span style="font-size: 11px; font-weight: 500; text-transform: uppercase; color: #64748B;">Cumulative GPA (CGPA)</span>
        <div class="mono" style="font-size: 15px; font-weight: 600; margin-top: 2px;">{{{{ student.cgpa }}}}</div>
      </div>
      <div>
        <span style="font-size: 11px; font-weight: 500; text-transform: uppercase; color: #64748B;">Degree Programme</span>
        <div style="font-size: 14px; margin-top: 2px;">{{{{ student.programme_name }}}} ({{{{ student.programme_code }}}})</div>
      </div>
      <div>
        <span style="font-size: 11px; font-weight: 500; text-transform: uppercase; color: #64748B;">School / Department</span>
        <div style="font-size: 14px; margin-top: 2px;">{{{{ student.dept_name }}}}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Hostel Accommodation Details</h2>
    <div style="margin-top: 10px;">
      {{% if room and room.room_number %}}
      <p>Allocated Room: <strong class="mono">{{{{ room.room_number }}}}</strong> in <strong>{{{{ room.block_name }}}}</strong></p>
      {{% else %}}
      <p>Status: <span class="badge badge-info">Day Scholar</span> (Non-Residential Student)</p>
      {{% endif %}}
    </div>
  </div>

  <div class="card">
    <h2>Enrolled Courses & Academic Record</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Course Code</th><th>Course Title</th><th>Credits</th><th>Status</th><th>Grade Points</th></tr></thead>
        <tbody>
          {{% for c in courses %}}
          <tr>
            <td class="mono">{{{{ c.course_code }}}}</td>
            <td>{{{{ c.course_title }}}}</td>
            <td class="mono">{{{{ c.credits }}}}</td>
            <td>
              <span class="badge {{{{ 'badge-success' if c.completion_status == 'COMPLETED' else 'badge-info' }}}}">
                {{{{ c.completion_status }}}}
              </span>
            </td>
            <td class="mono">{{{{ c.grade_points if c.grade_points is not none else 'N/A' }}}}</td>
          </tr>
          {{% else %}}
          <tr><td colspan="5">No courses currently enrolled.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  {{% if waitlists %}}
  <div class="card">
    <h2>Course Waitlist Applications</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Course Code</th><th>Course Title</th><th>Priority Queue Position</th><th>Status</th></tr></thead>
        <tbody>
          {{% for w in waitlists %}}
          <tr>
            <td class="mono">{{{{ w.course_code }}}}</td>
            <td>{{{{ w.course_title }}}}</td>
            <td class="mono"><span class="badge badge-warning">Position #{{{{ w.priority_position }}}}</span></td>
            <td><span class="badge badge-info">{{{{ w.status }}}}</span></td>
          </tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>
  {{% endif %}}

  <div class="card">
    <h2>Fee Invoices & Payment Ledger</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Invoice No</th><th>Description</th><th>Total (₹)</th><th>Paid (₹)</th><th>Due Date</th><th>Status</th></tr></thead>
        <tbody>
          {{% for f in fees %}}
          <tr>
            <td class="mono">{{{{ f.invoice_no }}}}</td>
            <td>Semester Tuition Fee</td>
            <td class="mono">{{{{ f.total_amount }}}}</td>
            <td class="mono">{{{{ f.paid_amount }}}}</td>
            <td class="mono">{{{{ f.due_date }}}}</td>
            <td>
              <span class="badge {{{{ 'badge-paid' if f.payment_status == 'PAID' else ('badge-partial' if f.payment_status == 'PARTIAL' else 'badge-overdue') }}}}">
                {{{{ f.payment_status }}}}
              </span>
            </td>
          </tr>
          {{% else %}}
          <tr><td colspan="6">No fee invoices recorded.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""


@student_bp.route("/dashboard", methods=["GET"])
@role_required(ROLE_STUDENT)
def student_dashboard():
    """Student Dashboard: displays personal profile, registered courses, available catalog for sign-up, hostel room, and fee invoices."""
    user = get_current_user()
    stu_id = user.get("entity_id") if user else None
    username = user.get("username") if user else None

    # Safe default student profile
    student_profile = {
        "student_id": stu_id or 1,
        "reg_no": username or "25BAI0077",
        "first_name": "Jacob",
        "last_name": "Jean",
        "email": "jacob.jean2025@vitstudent.ac.in",
        "cgpa": "9.45",
        "programme_name": "B.Tech in Computer Science and Engineering (AI & ML)",
        "programme_code": "BTECH-CSE-AIML",
        "dept_name": "School of Computer Science and Engineering",
    }
    courses = []
    room_info = None
    fees = []
    waitlists = []
    available_courses = []

    try:
        # Resolve student profile
        students = execute_query(
            "SELECT s.*, p.programme_name, p.programme_code, d.dept_name "
            "FROM STUDENT s "
            "JOIN PROGRAMME p ON s.programme_id = p.programme_id "
            "JOIN DEPARTMENT d ON p.dept_id = d.dept_id "
            "WHERE s.student_id = %s OR s.reg_no = %s LIMIT 1;",
            (stu_id or 1, username or "25BAI0077"),
        )
        if students:
            student_profile = dict(students[0])
    except Exception as e:
        print("[Student] Error resolving student profile:", e)

    curr_id = student_profile.get("student_id") or stu_id or 1

    try:
        # Query enrolled courses with credits and grade points
        courses = execute_query(
            "SELECT c.course_id, c.course_code, c.course_title, c.credits, e.completion_status, e.grade_points "
            "FROM ENROLLMENT e "
            "JOIN COURSE c ON e.course_id = c.course_id "
            "WHERE e.student_id = %s "
            "ORDER BY c.course_code;",
            (curr_id,),
        ) or []
    except Exception as e:
        print("[Student] Error resolving enrolled courses:", e)

    try:
        # Query hostel room allocation
        if student_profile.get("room_id") is not None:
            rooms = execute_query(
                "SELECT hr.room_number, hb.block_name "
                "FROM STUDENT s "
                "JOIN HOSTEL_ROOM hr ON s.room_id = hr.room_id "
                "JOIN HOSTEL_BLOCK hb ON hr.block_id = hb.block_id "
                "WHERE s.student_id = %s;",
                (curr_id,),
            )
            if rooms:
                room_info = rooms[0]
    except Exception as e:
        print("[Student] Error resolving hostel room:", e)

    try:
        # Query fee invoices
        fees = execute_query(
            "SELECT * FROM FEE_PAYMENT WHERE student_id = %s ORDER BY payment_id;",
            (curr_id,),
        ) or []
    except Exception as e:
        print("[Student] Error resolving fee payments:", e)

    try:
        # Query course waitlists
        waitlists = execute_query(
            "SELECT cw.waitlist_id, cw.course_id, cw.priority_position, cw.status, cw.waitlist_time, "
            "c.course_code, c.course_title "
            "FROM COURSE_WAITLIST cw "
            "JOIN COURSE c ON cw.course_id = c.course_id "
            "WHERE cw.student_id = %s AND cw.status = 'ACTIVE' "
            "ORDER BY cw.priority_position;",
            (curr_id,),
        ) or []
    except Exception as e:
        print("[Student] Error resolving course waitlists:", e)

    try:
        # Query full catalog of courses for enrollment / waitlisting
        catalog = execute_query(
            "SELECT c.*, d.dept_name, d.dept_code, p.course_code AS prereq_code "
            "FROM COURSE c "
            "JOIN DEPARTMENT d ON c.dept_id = d.dept_id "
            "LEFT JOIN COURSE p ON c.prereq_course_id = p.course_id "
            "ORDER BY c.course_code;"
        ) or []

        enrolled_course_ids = {c.get("course_id") for c in courses}
        waitlisted_course_ids = {w.get("course_id"): w.get("priority_position") for w in waitlists}

        for item in catalog:
            cid = item.get("course_id")
            item_copy = dict(item)
            item_copy["is_enrolled"] = cid in enrolled_course_ids
            item_copy["is_waitlisted"] = cid in waitlisted_course_ids
            item_copy["waitlist_pos"] = waitlisted_course_ids.get(cid)
            item_copy["available_seats"] = int(item.get("available_seats") or 0)
            available_courses.append(item_copy)
    except Exception as e:
        print("[Student] Error resolving course catalog:", e)

    try:
        return render_template(
            "student/dashboard.html",
            student=student_profile,
            courses=courses,
            room=room_info,
            fees=fees,
            waitlists=waitlists,
            available_courses=available_courses,
        ), 200
    except TemplateNotFound:
        return render_template_string(
            STUDENT_DASHBOARD_HTML,
            student=student_profile,
            courses=courses,
            room=room_info,
            fees=fees,
            waitlists=waitlists,
            available_courses=available_courses,
        ), 200


@student_bp.route("/courses/enroll", methods=["POST"])
@role_required(ROLE_STUDENT)
def student_enroll_course():
    """Enroll student into an available course offering."""
    user = get_current_user()
    stu_id = user.get("entity_id") or 1
    raw_course_id = request.form.get("course_id")
    try:
        course_id = int(raw_course_id)
    except (TypeError, ValueError):
        flash("Invalid course selection.", "danger")
        return redirect(url_for("student.student_dashboard"))

    # Check if already enrolled
    existing = execute_query(
        "SELECT * FROM ENROLLMENT WHERE student_id = %s AND course_id = %s;",
        (stu_id, course_id),
        fetch_one=True,
    )
    if existing:
        flash("You are already enrolled in this course.", "warning")
        return redirect(url_for("student.student_dashboard"))

    # Check prerequisite
    course = execute_query(
        "SELECT c.*, p.course_code AS prereq_code FROM COURSE c LEFT JOIN COURSE p ON c.prereq_course_id = p.course_id WHERE c.course_id = %s;",
        (course_id,),
        fetch_one=True,
    )
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("student.student_dashboard"))

    prereq_id = course.get("prereq_course_id")
    if prereq_id:
        prereq_completed = execute_query(
            "SELECT * FROM ENROLLMENT WHERE student_id = %s AND course_id = %s AND completion_status = 'COMPLETED';",
            (stu_id, prereq_id),
            fetch_one=True,
        )
        if not prereq_completed:
            prereq_name = course.get("prereq_code") or f"Course #{prereq_id}"
            flash(f"Prerequisite course {prereq_name} must be completed before enrolling in {course.get('course_code')}.", "danger")
            return redirect(url_for("student.student_dashboard"))

    # Check seat capacity
    avail = int(course.get("available_seats") or 0)
    if avail <= 0:
        flash(f"{course.get('course_code')} has no available seats. You can join the waitlist instead.", "warning")
        return redirect(url_for("student.student_dashboard"))

    # Find active semester
    sem = execute_query("SELECT semester_id FROM SEMESTER WHERE is_active = 1 LIMIT 1;", fetch_one=True)
    semester_id = sem.get("semester_id") if sem else 1

    try:
        execute_query(
            "INSERT INTO ENROLLMENT (student_id, course_id, semester_id, enrollment_date, completion_status) "
            "VALUES (%s, %s, %s, CURDATE(), 'ENROLLED');",
            (stu_id, course_id, semester_id),
            commit=True,
        )
        execute_query(
            "UPDATE COURSE SET available_seats = available_seats - 1 WHERE course_id = %s;",
            (course_id,),
            commit=True,
        )
        execute_query(
            "DELETE FROM COURSE_WAITLIST WHERE student_id = %s AND course_id = %s;",
            (stu_id, course_id),
            commit=True,
        )
        flash(f"Successfully signed up for {course.get('course_code')} &mdash; {course.get('course_title')}!", "success")
    except Exception as e:
        flash(f"Failed to enroll in course: {str(e)}", "danger")

    return redirect(url_for("student.student_dashboard"))


@student_bp.route("/courses/waitlist", methods=["POST"])
@role_required(ROLE_STUDENT)
def student_waitlist_course():
    """Add student to waitlist for a full course."""
    user = get_current_user()
    stu_id = user.get("entity_id") or 1
    raw_course_id = request.form.get("course_id")
    try:
        course_id = int(raw_course_id)
    except (TypeError, ValueError):
        flash("Invalid course selection.", "danger")
        return redirect(url_for("student.student_dashboard"))

    enrolled = execute_query(
        "SELECT * FROM ENROLLMENT WHERE student_id = %s AND course_id = %s;",
        (stu_id, course_id),
        fetch_one=True,
    )
    if enrolled:
        flash("You are already enrolled in this course.", "info")
        return redirect(url_for("student.student_dashboard"))

    existing = execute_query(
        "SELECT * FROM COURSE_WAITLIST WHERE student_id = %s AND course_id = %s AND status = 'ACTIVE';",
        (stu_id, course_id),
        fetch_one=True,
    )
    if existing:
        flash(f"You are already on the waitlist at priority position #{existing.get('priority_position')}.", "warning")
        return redirect(url_for("student.student_dashboard"))

    pos_row = execute_query(
        "SELECT COALESCE(MAX(priority_position), 0) + 1 AS next_pos FROM COURSE_WAITLIST WHERE course_id = %s AND status = 'ACTIVE';",
        (course_id,),
        fetch_one=True,
    )
    next_pos = int(pos_row.get("next_pos") if pos_row else 1)

    course = execute_query("SELECT course_code, course_title FROM COURSE WHERE course_id = %s;", (course_id,), fetch_one=True)
    c_code = course.get("course_code") if course else f"Course #{course_id}"

    try:
        execute_query(
            "INSERT INTO COURSE_WAITLIST (student_id, course_id, waitlist_time, priority_position, status) "
            "VALUES (%s, %s, NOW(), %s, 'ACTIVE');",
            (stu_id, course_id, next_pos),
            commit=True,
        )
        flash(f"Successfully joined waitlist for {c_code} at priority position #{next_pos}.", "success")
    except Exception as e:
        flash(f"Failed to join waitlist: {str(e)}", "danger")

    return redirect(url_for("student.student_dashboard"))

