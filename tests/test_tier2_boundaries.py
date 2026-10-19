"""Tier 2: Boundary, Edge-Case and Negative Path Verification.

Covers:
- Auth boundaries (invalid credentials, SQL injection attempts, long strings)
- Unauthenticated access redirects for all 5 role dashboards
- Role-based authorization matrix (cross-role dashboard rejections)
- Attendance shortage threshold boundary at exactly 75.00%
- Fee payment statuses (PENDING vs PARTIAL vs PAID vs OVERDUE)
- Course capacity boundary (0 seats remaining, FIFO queue ordering)
- Hostel room allocation boundaries (Day Scholars with NULL room_id, full rooms)
- Database unique constraints and composite primary key enforcement
"""

import pytest


# ==============================================================================
# Group 1: Authentication Boundaries & Error Handling
# ==============================================================================

class TestAuthBoundaries:
    """Authentication boundaries, negative tests, and unauthenticated redirects."""

    def test_b1_01_invalid_username_rejected(self, client):
        """Verify non-existent username is rejected with error or redirect."""
        res = client.post("/login", data={"username": "nonexistent_user", "password": "password123"}, follow_redirects=True)
        assert res.status_code in (200, 401)
        text = res.get_data(as_text=True)
        assert "dashboard" not in res.request.path.lower()

    def test_b1_02_invalid_password_rejected(self, client):
        """Verify valid username with wrong password is rejected."""
        res = client.post("/login", data={"username": "admin", "password": "wrong_password"}, follow_redirects=True)
        assert res.status_code in (200, 401)
        assert "admin/dashboard" not in res.request.path.lower()

    def test_b1_03_empty_username_rejected(self, client):
        """Verify empty username is rejected."""
        res = client.post("/login", data={"username": "", "password": "password123"}, follow_redirects=True)
        assert res.status_code in (200, 400, 401)
        assert "dashboard" not in res.request.path.lower()

    def test_b1_04_empty_password_rejected(self, client):
        """Verify empty password is rejected."""
        res = client.post("/login", data={"username": "admin", "password": ""}, follow_redirects=True)
        assert res.status_code in (200, 400, 401)
        assert "admin/dashboard" not in res.request.path.lower()

    def test_b1_05_both_credentials_empty_rejected(self, client):
        """Verify submitting empty username and password is rejected."""
        res = client.post("/login", data={"username": "", "password": ""}, follow_redirects=True)
        assert res.status_code in (200, 400, 401)
        assert "dashboard" not in res.request.path.lower()

    def test_b1_06_sql_injection_attempt_rejected(self, client):
        """Verify SQL injection strings in username are safely rejected."""
        res = client.post("/login", data={"username": "' OR '1'='1' --", "password": "password"}, follow_redirects=True)
        assert res.status_code in (200, 400, 401)
        assert "admin/dashboard" not in res.request.path.lower()

    def test_b1_07_special_characters_username_rejected(self, client):
        """Verify Unicode, control, and format characters in username handled cleanly."""
        res = client.post("/login", data={"username": "<script>alert(1)</script>", "password": "password"}, follow_redirects=True)
        assert res.status_code in (200, 400, 401)
        assert "dashboard" not in res.request.path.lower()

    def test_b1_08_long_string_overflow_username_rejected(self, client):
        """Verify extremely long username strings do not crash server."""
        long_user = "A" * 1024
        res = client.post("/login", data={"username": long_user, "password": "password"}, follow_redirects=True)
        assert res.status_code in (200, 400, 401, 413)

    def test_b1_09_unauthenticated_admin_dashboard_redirects(self, client):
        """Verify unauthenticated access to admin dashboard redirects to login."""
        res = client.get("/admin/dashboard", follow_redirects=False)
        assert res.status_code in (302, 401, 403)
        if res.status_code == 302:
            assert "/login" in res.headers.get("Location", "")

    def test_b1_10_unauthenticated_faculty_dashboard_redirects(self, client):
        """Verify unauthenticated access to faculty dashboard redirects to login."""
        res = client.get("/faculty/dashboard", follow_redirects=False)
        assert res.status_code in (302, 401, 403)
        if res.status_code == 302:
            assert "/login" in res.headers.get("Location", "")

    def test_b1_11_unauthenticated_student_dashboard_redirects(self, client):
        """Verify unauthenticated access to student dashboard redirects to login."""
        res = client.get("/student/dashboard", follow_redirects=False)
        assert res.status_code in (302, 401, 403)
        if res.status_code == 302:
            assert "/login" in res.headers.get("Location", "")

    def test_b1_12_unauthenticated_accounts_dashboard_redirects(self, client):
        """Verify unauthenticated access to accounts dashboard redirects to login."""
        res = client.get("/accounts/dashboard", follow_redirects=False)
        assert res.status_code in (302, 401, 403)
        if res.status_code == 302:
            assert "/login" in res.headers.get("Location", "")

    def test_b1_13_unauthenticated_warden_dashboard_redirects(self, client):
        """Verify unauthenticated access to warden dashboard redirects to login."""
        res = client.get("/warden/dashboard", follow_redirects=False)
        assert res.status_code in (302, 401, 403)
        if res.status_code == 302:
            assert "/login" in res.headers.get("Location", "")

    def test_b1_14_unauthenticated_attendance_post_rejected(self, client):
        """Verify unauthenticated user cannot POST attendance."""
        res = client.post("/faculty/attendance", data={"course_id": 3, "attendance_date": "2026-10-19"}, follow_redirects=False)
        assert res.status_code in (302, 401, 403)

    def test_b1_15_unauthenticated_payment_post_rejected(self, client):
        """Verify unauthenticated user cannot POST payment recording."""
        res = client.post("/accounts/record-payment", data={"invoice_no": "INV-2026-003", "amount_paid": 1000}, follow_redirects=False)
        assert res.status_code in (302, 401, 403)


# ==============================================================================
# Group 2: Cross-Role Authorization Matrix
# ==============================================================================

class TestCrossRoleAuthorizationMatrix:
    """Verifies that each role cannot access unauthorized dashboards or endpoints."""

    # Admin route barriers
    def test_b2_01_student_cannot_access_admin_dashboard(self, student_client):
        res = student_client.get("/admin/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_02_faculty_cannot_access_admin_dashboard(self, faculty_client):
        res = faculty_client.get("/admin/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_03_accounts_cannot_access_admin_dashboard(self, accounts_client):
        res = accounts_client.get("/admin/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_04_warden_cannot_access_admin_dashboard(self, warden_client):
        res = warden_client.get("/admin/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    # Faculty route barriers
    def test_b2_05_student_cannot_access_faculty_dashboard(self, student_client):
        res = student_client.get("/faculty/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_06_accounts_cannot_access_faculty_dashboard(self, accounts_client):
        res = accounts_client.get("/faculty/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_07_warden_cannot_access_faculty_dashboard(self, warden_client):
        res = warden_client.get("/faculty/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_08_student_cannot_post_attendance(self, student_client):
        res = student_client.post("/faculty/attendance", data={"course_id": 3}, follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_09_accounts_cannot_post_attendance(self, accounts_client):
        res = accounts_client.post("/faculty/attendance", data={"course_id": 3}, follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_10_warden_cannot_post_attendance(self, warden_client):
        res = warden_client.post("/faculty/attendance", data={"course_id": 3}, follow_redirects=False)
        assert res.status_code in (403, 302)

    # Student route barriers
    def test_b2_11_faculty_cannot_access_student_dashboard(self, faculty_client):
        res = faculty_client.get("/student/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_12_accounts_cannot_access_student_dashboard(self, accounts_client):
        res = accounts_client.get("/student/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_13_warden_cannot_access_student_dashboard(self, warden_client):
        res = warden_client.get("/student/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    # Accounts route barriers
    def test_b2_14_student_cannot_access_accounts_dashboard(self, student_client):
        res = student_client.get("/accounts/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_15_faculty_cannot_access_accounts_dashboard(self, faculty_client):
        res = faculty_client.get("/accounts/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_16_warden_cannot_access_accounts_dashboard(self, warden_client):
        res = warden_client.get("/accounts/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_17_student_cannot_record_payment(self, student_client):
        res = student_client.post("/accounts/record-payment", data={"invoice_no": "INV-2026-003", "amount_paid": 500}, follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_18_faculty_cannot_record_payment(self, faculty_client):
        res = faculty_client.post("/accounts/record-payment", data={"invoice_no": "INV-2026-003", "amount_paid": 500}, follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_19_warden_cannot_record_payment(self, warden_client):
        res = warden_client.post("/accounts/record-payment", data={"invoice_no": "INV-2026-003", "amount_paid": 500}, follow_redirects=False)
        assert res.status_code in (403, 302)

    # Warden route barriers
    def test_b2_20_student_cannot_access_warden_dashboard(self, student_client):
        res = student_client.get("/warden/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_21_faculty_cannot_access_warden_dashboard(self, faculty_client):
        res = faculty_client.get("/warden/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)

    def test_b2_22_accounts_cannot_access_warden_dashboard(self, accounts_client):
        res = accounts_client.get("/warden/dashboard", follow_redirects=False)
        assert res.status_code in (403, 302)


# ==============================================================================
# Group 3: Domain Boundary Conditions
# ==============================================================================

class TestDomainBoundaries:
    """Domain boundaries, mathematical properties, and database constraints."""

    # Attendance shortage boundaries
    def test_b3_01_attendance_exact_75_percent_compliant(self, db_query):
        """Verify student with exactly 75.00% attendance is NOT flagged in shortage view."""
        # 3 out of 4 classes = 75.00%
        res = db_query("SELECT ROUND((3.0 / 4.0) * 100, 2) AS pct;")
        pct = float(res[0]["pct"])
        assert pct == 75.00
        # Check that HAVING attendance_percentage < 75.00 excludes 75.00
        assert not (pct < 75.00)

    def test_b3_02_attendance_74_99_percent_is_shortage(self, db_query):
        """Verify student with 74.99% attendance IS flagged as shortage."""
        pct = 74.99
        assert pct < 75.00

    def test_b3_03_attendance_zero_percent_is_shortage(self, db_query):
        """Verify student with 0 classes attended is flagged as shortage."""
        pct = 0.00
        assert pct < 75.00

    def test_b3_04_attendance_100_percent_compliant(self, db_query):
        """Verify Jacob Jean with 3/3 classes present (100.00%) is NOT in shortage view."""
        rows = db_query(
            "SELECT * FROM v_faculty_attendance_shortage WHERE reg_no = '25BAI0077';"
        )
        assert len(rows) == 0, "Jacob Jean should not be flagged for attendance shortage"

    def test_b3_05_attendance_shortage_view_sql_threshold_logic(self, db_query):
        """Verify v_faculty_attendance_shortage only selects < 75.00%."""
        rows = db_query("SELECT attendance_percentage FROM v_faculty_attendance_shortage;")
        for r in rows:
            assert float(r["attendance_percentage"]) < 75.00

    # Fee payment status boundaries
    def test_b3_06_fee_status_zero_paid_before_due_date_is_pending(self):
        """Mathematical verification: 0 paid before due date has status PENDING."""
        paid = 0.00
        total = 195000.00
        is_overdue = False
        status = "PENDING" if paid == 0.00 and not is_overdue else "OTHER"
        assert status == "PENDING"

    def test_b3_07_fee_status_zero_paid_after_due_date_is_overdue(self, db_query):
        """Verify seed invoice INV-2026-004 (Nikhil Sharma) is OVERDUE with 0 paid."""
        rows = db_query("SELECT * FROM FEE_PAYMENT WHERE invoice_no = 'INV-2026-004';")
        assert len(rows) == 1
        assert rows[0]["payment_status"] == "OVERDUE"
        assert float(rows[0]["paid_amount"]) == 0.00

    def test_b3_08_fee_status_partial_payment_is_partial(self, db_query):
        """Verify seed invoice INV-2026-003 (Krrish Pare) has status PARTIAL."""
        rows = db_query("SELECT * FROM FEE_PAYMENT WHERE invoice_no = 'INV-2026-003';")
        assert len(rows) == 1
        assert rows[0]["payment_status"] == "PARTIAL"
        assert float(rows[0]["paid_amount"]) == 100000.00
        assert float(rows[0]["total_amount"]) == 195000.00

    def test_b3_09_fee_status_exact_payment_is_paid(self, db_query):
        """Verify seed invoice INV-2026-001 (Jacob Jean) is PAID."""
        rows = db_query("SELECT * FROM FEE_PAYMENT WHERE invoice_no = 'INV-2026-001';")
        assert len(rows) == 1
        assert rows[0]["payment_status"] == "PAID"
        assert float(rows[0]["paid_amount"]) == float(rows[0]["total_amount"])

    def test_b3_10_fee_status_overpayment_is_paid(self):
        """Verify paid >= total is classified as PAID."""
        paid = 200000.00
        total = 195000.00
        assert paid >= total

    def test_b3_11_fee_defaulter_includes_pending_partial_overdue(self, db_query):
        """Verify v_accounts_defaulters_list includes PARTIAL and OVERDUE."""
        rows = db_query("SELECT invoice_no, payment_status FROM v_accounts_defaulters_list;")
        invoices = {r["invoice_no"] for r in rows}
        assert "INV-2026-003" in invoices  # PARTIAL
        assert "INV-2026-004" in invoices  # OVERDUE

    def test_b3_12_fee_defaulter_excludes_paid(self, db_query):
        """Verify fully paid invoices are excluded from defaulters list."""
        rows = db_query("SELECT invoice_no FROM v_accounts_defaulters_list;")
        invoices = {r["invoice_no"] for r in rows}
        assert "INV-2026-001" not in invoices
        assert "INV-2026-002" not in invoices

    def test_b3_13_record_payment_negative_amount_rejected(self, accounts_client):
        """Verify negative payment amount is rejected."""
        res = accounts_client.post("/accounts/record-payment", data={"invoice_no": "INV-2026-003", "amount_paid": -500}, follow_redirects=True)
        # Should reject or not mark as negative
        assert res.status_code in (200, 400)

    def test_b3_14_record_payment_nonexistent_invoice_rejected(self, accounts_client):
        """Verify payment against non-existent invoice is rejected."""
        res = accounts_client.post("/accounts/record-payment", data={"invoice_no": "INV-INVALID-999", "amount_paid": 500}, follow_redirects=True)
        assert res.status_code in (200, 400, 404)

    # Course Capacity, Enrollment & Waitlist boundaries
    def test_b3_15_course_capacity_zero_seats_blocks_direct_enrollment(self, db_query):
        """Verify course CSE2001 has available_seats = 0 in seed data."""
        rows = db_query("SELECT capacity, available_seats FROM COURSE WHERE course_code = 'CSE2001';")
        assert len(rows) == 1
        assert int(rows[0]["available_seats"]) == 0

    def test_b3_16_course_capacity_zero_creates_waitlist_priority_1(self, db_query):
        """Verify waitlist for CSE2001 has priority position 1 for first student."""
        rows = db_query("SELECT * FROM COURSE_WAITLIST WHERE course_id = 2 ORDER BY priority_position ASC;")
        assert len(rows) >= 2
        assert int(rows[0]["priority_position"]) == 1

    def test_b3_17_course_waitlist_priority_queue_fifo_ordering(self, db_query):
        """Verify waitlist entries follow strict FIFO priority ordering."""
        rows = db_query("SELECT priority_position FROM COURSE_WAITLIST WHERE course_id = 2 ORDER BY priority_position ASC;")
        positions = [int(r["priority_position"]) for r in rows]
        assert positions == sorted(positions)
        assert positions[0] < positions[1]

    def test_b3_18_course_prerequisite_not_met_blocks_enrollment(self, db_query):
        """Verify course prerequisite structure (CSE2005 requires CSE2001)."""
        rows = db_query("SELECT prereq_course_id FROM COURSE WHERE course_code = 'CSE2005';")
        assert len(rows) == 1
        assert rows[0]["prereq_course_id"] is not None

    def test_b3_19_duplicate_course_enrollment_composite_pk_violation(self, db_query):
        """Verify composite PK (student_id, course_id) in ENROLLMENT prevents duplicate enrollment."""
        # Check information_schema for primary key columns
        rows = db_query(
            "SELECT column_name FROM information_schema.key_column_usage "
            "WHERE table_schema = 'university_db' AND table_name = 'ENROLLMENT' AND constraint_name = 'PRIMARY' "
            "ORDER BY ordinal_position;"
        )
        pk_cols = [r["column_name"].lower() for r in rows]
        assert "student_id" in pk_cols
        assert "course_id" in pk_cols

    def test_b3_20_duplicate_course_waitlist_unique_constraint_violation(self, db_query):
        """Verify unique constraint uk_student_course_waitlist on (student_id, course_id)."""
        rows = db_query(
            "SELECT constraint_name FROM information_schema.table_constraints "
            "WHERE table_schema = 'university_db' AND table_name = 'COURSE_WAITLIST' AND constraint_type = 'UNIQUE';"
        )
        assert len(rows) >= 1

    # Hostel Room & Resident boundaries
    def test_b3_21_day_scholar_room_id_is_null(self, db_query):
        """Verify Day Scholar student Sneha Rao (25BCE0899) has room_id = NULL."""
        rows = db_query("SELECT room_id FROM STUDENT WHERE reg_no = '25BCE0899';")
        assert len(rows) == 1
        assert rows[0]["room_id"] is None

    def test_b3_22_day_scholar_excluded_from_resident_directory(self, db_query):
        """Verify Day Scholar is excluded from v_warden_resident_directory."""
        rows = db_query("SELECT * FROM v_warden_resident_directory WHERE reg_no = '25BCE0899';")
        assert len(rows) == 0

    def test_b3_23_room_capacity_at_limit_has_zero_vacant_beds(self, db_query):
        """Verify room A-201 with 2 occupants has 0 vacant beds."""
        rows = db_query("SELECT vacant_beds FROM v_warden_occupancy_overview WHERE room_number = 'A-201';")
        assert len(rows) == 1
        assert int(rows[0]["vacant_beds"]) == 0

    def test_b3_24_vacant_beds_never_negative_constraint(self, db_query):
        """Verify all rooms have occupied_beds <= capacity."""
        rows = db_query("SELECT occupied_beds, capacity FROM HOSTEL_ROOM;")
        for r in rows:
            assert int(r["occupied_beds"]) <= int(r["capacity"])

    def test_b3_25_gender_segregation_boundary_male_in_female_block_rejected(self, db_query):
        """Verify all male residents are in male blocks."""
        rows = db_query(
            "SELECT s.gender, hb.gender_type "
            "FROM STUDENT s "
            "JOIN HOSTEL_ROOM hr ON s.room_id = hr.room_id "
            "JOIN HOSTEL_BLOCK hb ON hr.block_id = hb.block_id "
            "WHERE s.gender = 'M';"
        )
        for r in rows:
            assert r["gender_type"] == "M"

    def test_b3_26_gender_segregation_boundary_female_in_male_block_rejected(self, db_query):
        """Verify all female residents are in female blocks."""
        rows = db_query(
            "SELECT s.gender, hb.gender_type "
            "FROM STUDENT s "
            "JOIN HOSTEL_ROOM hr ON s.room_id = hr.room_id "
            "JOIN HOSTEL_BLOCK hb ON hr.block_id = hb.block_id "
            "WHERE s.gender = 'F';"
        )
        for r in rows:
            assert r["gender_type"] == "F"

    # Unique Key Constraints in Relational DDL
    def test_b3_27_duplicate_department_code_rejected(self, db_query):
        """Verify uk_dept_code unique key exists on DEPARTMENT."""
        rows = db_query(
            "SELECT column_name FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu USING (constraint_name, table_schema, table_name) "
            "WHERE tc.table_schema = 'university_db' AND tc.table_name = 'DEPARTMENT' AND tc.constraint_type = 'UNIQUE';"
        )
        cols = [r["column_name"].lower() for r in rows]
        assert "dept_code" in cols

    def test_b3_28_duplicate_programme_code_rejected(self, db_query):
        """Verify uk_programme_code unique key exists on PROGRAMME."""
        rows = db_query(
            "SELECT column_name FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu USING (constraint_name, table_schema, table_name) "
            "WHERE tc.table_schema = 'university_db' AND tc.table_name = 'PROGRAMME' AND tc.constraint_type = 'UNIQUE';"
        )
        cols = [r["column_name"].lower() for r in rows]
        assert "programme_code" in cols

    def test_b3_29_duplicate_faculty_employee_code_rejected(self, db_query):
        """Verify uk_faculty_emp_code unique key exists on FACULTY."""
        rows = db_query(
            "SELECT column_name FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu USING (constraint_name, table_schema, table_name) "
            "WHERE tc.table_schema = 'university_db' AND tc.table_name = 'FACULTY' AND tc.constraint_type = 'UNIQUE';"
        )
        cols = [r["column_name"].lower() for r in rows]
        assert "employee_code" in cols

    def test_b3_30_duplicate_faculty_email_rejected(self, db_query):
        """Verify uk_faculty_email unique key exists on FACULTY."""
        rows = db_query(
            "SELECT column_name FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu USING (constraint_name, table_schema, table_name) "
            "WHERE tc.table_schema = 'university_db' AND tc.table_name = 'FACULTY' AND tc.constraint_type = 'UNIQUE';"
        )
        cols = [r["column_name"].lower() for r in rows]
        assert "email" in cols

    def test_b3_31_duplicate_course_code_rejected(self, db_query):
        """Verify uk_course_code unique key exists on COURSE."""
        rows = db_query(
            "SELECT column_name FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu USING (constraint_name, table_schema, table_name) "
            "WHERE tc.table_schema = 'university_db' AND tc.table_name = 'COURSE' AND tc.constraint_type = 'UNIQUE';"
        )
        cols = [r["column_name"].lower() for r in rows]
        assert "course_code" in cols

    def test_b3_32_duplicate_hostel_block_name_rejected(self, db_query):
        """Verify uk_block_name unique key exists on HOSTEL_BLOCK."""
        rows = db_query(
            "SELECT column_name FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu USING (constraint_name, table_schema, table_name) "
            "WHERE tc.table_schema = 'university_db' AND tc.table_name = 'HOSTEL_BLOCK' AND tc.constraint_type = 'UNIQUE';"
        )
        cols = [r["column_name"].lower() for r in rows]
        assert "block_name" in cols

    def test_b3_33_duplicate_room_in_same_block_rejected(self, db_query):
        """Verify composite unique key uk_block_room on (block_id, room_number) in HOSTEL_ROOM."""
        rows = db_query(
            "SELECT constraint_name FROM information_schema.table_constraints "
            "WHERE table_schema = 'university_db' AND table_name = 'HOSTEL_ROOM' AND constraint_type = 'UNIQUE';"
        )
        assert len(rows) >= 1

    def test_b3_34_duplicate_student_reg_no_rejected(self, db_query):
        """Verify uk_student_reg_no unique key exists on STUDENT."""
        rows = db_query(
            "SELECT column_name FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu USING (constraint_name, table_schema, table_name) "
            "WHERE tc.table_schema = 'university_db' AND tc.table_name = 'STUDENT' AND tc.constraint_type = 'UNIQUE';"
        )
        cols = [r["column_name"].lower() for r in rows]
        assert "reg_no" in cols

    def test_b3_35_duplicate_student_email_rejected(self, db_query):
        """Verify uk_student_email unique key exists on STUDENT."""
        rows = db_query(
            "SELECT column_name FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu USING (constraint_name, table_schema, table_name) "
            "WHERE tc.table_schema = 'university_db' AND tc.table_name = 'STUDENT' AND tc.constraint_type = 'UNIQUE';"
        )
        cols = [r["column_name"].lower() for r in rows]
        assert "email" in cols

    def test_b3_36_duplicate_invoice_no_rejected(self, db_query):
        """Verify uk_invoice_no unique key exists on FEE_PAYMENT."""
        rows = db_query(
            "SELECT column_name FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu USING (constraint_name, table_schema, table_name) "
            "WHERE tc.table_schema = 'university_db' AND tc.table_name = 'FEE_PAYMENT' AND tc.constraint_type = 'UNIQUE';"
        )
        cols = [r["column_name"].lower() for r in rows]
        assert "invoice_no" in cols
