"""Tier 5: CRUD operations, server-side search and input validation (Review 3).

Each test drives the real Flask routes against the configured MySQL database and
checks the resulting rows. The database is re-seeded before and after this module
so the other tiers always see the Section 4 sample data.
"""

import datetime
import os
import re
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.db import execute_query
from schema.init_db import apply_schema, apply_seed_data, apply_views

FUTURE_DUE = (datetime.date.today() + datetime.timedelta(days=60)).isoformat()


def reseed():
    apply_schema()
    apply_views()
    apply_seed_data()


@pytest.fixture(scope="module", autouse=True)
def fresh_database():
    reseed()
    yield
    reseed()


@pytest.fixture(scope="module")
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


def login(app, username, password):
    client = app.test_client()
    res = client.post("/login", data={"username": username, "password": password})
    return client, res.status_code


def post(client, url, data=None):
    """POSTs a form and returns the flashed messages shown on the page it redirects to."""
    res = client.post(url, data=data or {}, follow_redirects=True)
    msgs = re.findall(r'<div class="alert [^"]*" role="alert">\s*<span>(.*?)</span>', res.get_data(as_text=True), re.S)
    return " | ".join(m.strip() for m in msgs)


def one(sql, params=()):
    return execute_query(sql, params, fetch_one=True)


def count(sql, params=()):
    return int(one(sql, params)["n"])


# ---------------------------------------------------------------- authentication
@pytest.mark.parametrize("username,password,expected", [
    ("admin", "admin123", 302),
    ("EMP1002", "password", 302),
    ("25BAI0030", "password", 302),
    ("ramesh.kumar@vit.ac.in", "faculty123", 302),
    ("admin", "password", 401),
    ("admin", "student123", 401),
    ("accounts", "warden123", 401),
    ("warden", "password", 401),
])
def test_each_account_accepts_only_its_own_password(app, username, password, expected):
    assert login(app, username, password)[1] == expected


# ---------------------------------------------------------------- student CRUD
class TestStudentEnrollment:
    def test_enroll_decrements_seats(self, app):
        client, _ = login(app, "25BCE0899", "password")
        msg = post(client, "/student/courses/enroll", {"course_id": 4})
        assert "Successfully signed up for ECE1002" in msg
        assert count("SELECT COUNT(*) n FROM ENROLLMENT WHERE student_id = 5 AND course_id = 4") == 1
        assert one("SELECT available_seats FROM COURSE WHERE course_id = 4")["available_seats"] == 14

    def test_waitlist_rejected_while_seats_free(self, app):
        client, _ = login(app, "25BCE0899", "password")
        msg = post(client, "/student/courses/waitlist", {"course_id": 3})
        assert "still has open seats" in msg
        assert count("SELECT COUNT(*) n FROM COURSE_WAITLIST WHERE student_id = 5 AND course_id = 3") == 0

    def test_drop_deletes_enrollment_and_releases_seat(self, app):
        client, _ = login(app, "25BCE0899", "password")
        msg = post(client, "/student/courses/drop", {"course_id": 4})
        assert "Dropped ECE1002" in msg
        assert count("SELECT COUNT(*) n FROM ENROLLMENT WHERE student_id = 5 AND course_id = 4") == 0
        assert one("SELECT available_seats FROM COURSE WHERE course_id = 4")["available_seats"] == 15

    def test_completed_course_cannot_be_dropped(self, app):
        client, _ = login(app, "25BAI0077", "password")
        msg = post(client, "/student/courses/drop", {"course_id": 1})
        assert "cannot be dropped" in msg
        assert count("SELECT COUNT(*) n FROM ENROLLMENT WHERE student_id = 1 AND course_id = 1") == 1


# ---------------------------------------------------------------- accounts CRUD + validation
class TestAccountsInvoices:
    @pytest.fixture
    def client(self, app):
        return login(app, "accounts", "accounts123")[0]

    def test_negative_paid_amount_rejected(self, client):
        msg = post(client, "/accounts/add-dues", {"student_id": 5, "invoice_no": "INV-T-1", "total_amount": "1000",
                                                  "paid_amount": "-500", "due_date": FUTURE_DUE})
        assert "cannot be less than" in msg
        assert count("SELECT COUNT(*) n FROM FEE_PAYMENT WHERE invoice_no = 'INV-T-1'") == 0

    def test_paid_more_than_total_rejected(self, client):
        msg = post(client, "/accounts/add-dues", {"student_id": 5, "invoice_no": "INV-T-2", "total_amount": "1000",
                                                  "paid_amount": "1500", "due_date": FUTURE_DUE})
        assert "cannot be more than the total" in msg
        assert count("SELECT COUNT(*) n FROM FEE_PAYMENT WHERE invoice_no = 'INV-T-2'") == 0

    def test_past_due_date_rejected(self, client):
        msg = post(client, "/accounts/add-dues", {"student_id": 5, "invoice_no": "INV-T-4", "total_amount": "1000",
                                                  "paid_amount": "0", "due_date": "2020-01-01"})
        assert "Due date cannot be before" in msg

    def test_valid_invoice_created_as_pending(self, client):
        msg = post(client, "/accounts/add-dues", {"student_id": 5, "invoice_no": "inv-t-3", "total_amount": "1000",
                                                  "paid_amount": "0", "due_date": FUTURE_DUE})
        assert "issued successfully" in msg
        assert one("SELECT payment_status FROM FEE_PAYMENT WHERE invoice_no = 'INV-T-3'")["payment_status"] == "PENDING"

    def test_payment_on_paid_invoice_rejected(self, client):
        msg = post(client, "/accounts/record-payment", {"invoice_no": "INV-2026-001", "amount_paid": "50000"})
        assert "already fully paid" in msg
        assert one("SELECT paid_amount FROM FEE_PAYMENT WHERE invoice_no = 'INV-2026-001'")["paid_amount"] == 195000

    def test_overpayment_rejected(self, client):
        msg = post(client, "/accounts/record-payment", {"invoice_no": "INV-2026-003", "amount_paid": "95000.01"})
        assert "exceeds the outstanding balance" in msg
        assert one("SELECT paid_amount FROM FEE_PAYMENT WHERE invoice_no = 'INV-2026-003'")["paid_amount"] == 100000

    def test_part_payment_keeps_overdue_status(self, client):
        post(client, "/accounts/record-payment", {"invoice_no": "INV-2026-004", "amount_paid": "1000"})
        assert one("SELECT payment_status FROM FEE_PAYMENT WHERE invoice_no = 'INV-2026-004'")["payment_status"] == "OVERDUE"

    def test_exact_balance_marks_paid(self, client):
        post(client, "/accounts/record-payment", {"invoice_no": "INV-2026-003", "amount_paid": "95000"})
        assert one("SELECT payment_status FROM FEE_PAYMENT WHERE invoice_no = 'INV-2026-003'")["payment_status"] == "PAID"

    def test_invoice_with_payments_cannot_be_cancelled(self, client):
        msg = post(client, "/accounts/invoices/delete", {"invoice_no": "INV-2026-004"})
        assert "cannot be cancelled" in msg
        assert count("SELECT COUNT(*) n FROM FEE_PAYMENT WHERE invoice_no = 'INV-2026-004'") == 1

    def test_unpaid_invoice_cancel_deletes_row(self, client):
        msg = post(client, "/accounts/invoices/delete", {"invoice_no": "INV-T-3"})
        assert "cancelled" in msg
        assert count("SELECT COUNT(*) n FROM FEE_PAYMENT WHERE invoice_no = 'INV-T-3'") == 0


# ---------------------------------------------------------------- faculty attendance validation
class TestFacultyAttendance:
    @pytest.fixture
    def client(self, app):
        return login(app, "EMP1003", "password")[0]

    def test_student_not_enrolled_rejected(self, client):
        msg = post(client, "/faculty/attendance", {"course_id": 3, "student_id": 5, "status": "Present",
                                                   "attendance_date": "2026-08-07"})
        assert "not enrolled" in msg or "None of the selected students" in msg
        assert count("SELECT COUNT(*) n FROM ATTENDANCE WHERE student_id = 5") == 0

    def test_future_date_rejected(self, client):
        future = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        msg = post(client, "/faculty/attendance", {"course_id": 3, "student_id": 1, "status": "Present",
                                                   "attendance_date": future})
        assert "cannot be after" in msg
        assert count("SELECT COUNT(*) n FROM ATTENDANCE WHERE attendance_date = %s", (future,)) == 0

    def test_invalid_status_rejected(self, client):
        msg = post(client, "/faculty/attendance", {"course_id": 3, "student_id": 1, "status": "Maybe",
                                                   "attendance_date": "2026-08-07"})
        assert "must be one of" in msg

    def test_batch_sheet_records_enrolled_and_skips_others(self, client):
        msg = post(client, "/faculty/attendance", {"course_id": 3, "attendance_date": "2026-08-07",
                                                   "status_1": "Present", "status_3": "Absent", "status_5": "Present"})
        assert "recorded attendance for 2 student(s)" in msg and "1 student(s) skipped" in msg
        assert count("SELECT COUNT(*) n FROM ATTENDANCE WHERE attendance_date = '2026-08-07'") == 2


# ---------------------------------------------------------------- admin CRUD + validation + search
class TestAdminCourses:
    @pytest.fixture
    def client(self, app):
        return login(app, "admin", "admin123")[0]

    def test_negative_credits_rejected(self, client):
        msg = post(client, "/admin/courses/add", {"course_code": "CSE3001", "course_title": "Test", "credits": "-4",
                                                  "capacity": "-10", "dept_id": "1"})
        assert "Credits must be at least 1" in msg
        assert count("SELECT COUNT(*) n FROM COURSE WHERE course_code = 'CSE3001'") == 0

    def test_create_edit_delete_course(self, client):
        post(client, "/admin/courses/add", {"course_code": "cse3001", "course_title": "Software Engineering",
                                            "credits": "4", "capacity": "40", "dept_id": "1"})
        course_id = one("SELECT course_id FROM COURSE WHERE course_code = 'CSE3001'")["course_id"]

        post(client, f"/admin/courses/{course_id}/edit", {"course_title": "Software Engineering Lab",
                                                          "credits": "3", "capacity": "50"})
        row = one("SELECT course_title, credits, capacity, available_seats FROM COURSE WHERE course_id = %s", (course_id,))
        assert (row["course_title"], row["credits"], row["capacity"], row["available_seats"]) == \
            ("Software Engineering Lab", 3, 50, 50)

        msg = post(client, f"/admin/courses/{course_id}/delete")
        assert "deleted" in msg
        assert count("SELECT COUNT(*) n FROM COURSE WHERE course_id = %s", (course_id,)) == 0

    def test_capacity_cannot_go_below_seats_taken(self, client):
        msg = post(client, "/admin/courses/1/edit", {"course_title": "Problem Solving", "credits": "4", "capacity": "10"})
        assert "cannot be reduced below" in msg
        assert one("SELECT capacity FROM COURSE WHERE course_id = 1")["capacity"] == 60

    def test_course_with_enrolled_students_cannot_be_deleted(self, client):
        msg = post(client, "/admin/courses/3/delete")
        assert "cannot be deleted" in msg
        assert count("SELECT COUNT(*) n FROM COURSE WHERE course_id = 3") == 1


class TestAdminStudents:
    BASE = {"role": "student", "password": "password", "reg_no": "25BCE9998", "first_name": "Test", "last_name": "User",
            "email": "test.user@vitstudent.ac.in", "dob": "2005-01-01", "gender": "F", "cgpa": "8.5", "programme_id": "2"}

    @pytest.fixture
    def client(self, app):
        return login(app, "admin", "admin123")[0]

    @pytest.mark.parametrize("override,expected", [
        ({"room_id": "2"}, "does not accept students of gender"),
        ({"gender": "M", "room_id": "1"}, "is full"),
        ({"cgpa": "11"}, "CGPA must be between"),
        ({"reg_no": "BAD"}, "Registration number"),
        ({"email": "not-an-email"}, "Email"),
    ])
    def test_invalid_student_rejected(self, client, override, expected):
        msg = post(client, "/admin/users/add", dict(self.BASE, **override))
        assert expected in msg
        assert count("SELECT COUNT(*) n FROM STUDENT WHERE reg_no = %s", (override.get("reg_no", "25BCE9998"),)) == 0

    def test_add_then_delete_student(self, app, client):
        msg = post(client, "/admin/users/add", dict(self.BASE, room_id="3"))
        assert "successfully added" in msg
        assert one("SELECT occupied_beds FROM HOSTEL_ROOM WHERE room_id = 3")["occupied_beds"] == 2
        assert login(app, "25BCE9998", "password")[1] == 302

        student_id = one("SELECT student_id FROM STUDENT WHERE reg_no = '25BCE9998'")["student_id"]
        msg = post(client, f"/admin/students/{student_id}/delete")
        assert "deleted" in msg
        assert count("SELECT COUNT(*) n FROM STUDENT WHERE reg_no = '25BCE9998'") == 0
        assert count("SELECT COUNT(*) n FROM USER_ACCOUNT WHERE username = '25BCE9998'") == 0
        assert one("SELECT occupied_beds FROM HOSTEL_ROOM WHERE room_id = 3")["occupied_beds"] == 1

    def test_existing_account_not_overwritten(self, client):
        msg = post(client, "/admin/users/add", {"role": "warden", "password": "warden999", "username": "25BAI0030"})
        assert "already exists" in msg
        assert one("SELECT role FROM USER_ACCOUNT WHERE username = '25BAI0030'")["role"] == "student"


class TestAdminSearch:
    def test_search_finds_student_by_name(self, app):
        client, _ = login(app, "admin", "admin123")
        html = client.get("/admin/dashboard?q=krrish").get_data(as_text=True)
        assert "Results for" in html and "1 student(s)" in html and "25BAI0030" in html

    def test_search_finds_course_by_title(self, app):
        client, _ = login(app, "admin", "admin123")
        html = client.get("/admin/dashboard?q=database").get_data(as_text=True)
        assert "1 course(s)" in html

    def test_wildcard_characters_are_literal(self, app):
        client, _ = login(app, "admin", "admin123")
        html = client.get("/admin/dashboard?q=%25").get_data(as_text=True)
        assert "0 student(s), 0 course(s)" in html
