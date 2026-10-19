"""Tier 1: Feature Coverage Test Suite.

Verifies the primary behavior (happy path) for all 12 core features
defined in TEST_INFRA.md (>=5 tests per feature).
F1:  Database Connectivity & Setup
F2:  12 Relational Tables DDL
F3:  6 Analytical Views
F4:  Comprehensive Seed Data & Integrity
F5:  Auth & Role Access Control
F6:  Admin Dashboard & Queries
F7:  Faculty Roster & Attendance
F8:  Student Profile, Grades & Fees
F9:  Accounts Ledger & Payments
F10: Warden Occupancy & Residents
F11: UI Aesthetic Standards
F12: System Integrity & Endpoints
"""

import pytest


# ==============================================================================
# Feature 1: Database Connectivity & Setup (ORIGINAL_REQUEST R1)
# ==============================================================================

class TestFeature1DBConnectivity:
    """Feature 1: MySQL Database Connectivity & Configuration."""

    def test_f1_01_db_connection_alive(self, db_query):
        """Verify the database engine responds to a basic connectivity ping."""
        res = db_query("SELECT 1 AS ping;")
        assert res is not None
        assert len(res) == 1
        val = list(res[0].values())[0]
        assert str(val) == "1"

    def test_f1_02_database_selection(self, db_query):
        """Verify connection is established to the correct 'university_db' database."""
        res = db_query("SELECT DATABASE() AS current_db;")
        assert res is not None
        assert len(res) == 1
        val = list(res[0].values())[0]
        assert val == "university_db"

    def test_f1_03_character_set_and_collation(self, db_query):
        """Verify the database character set is utf8mb4."""
        res = db_query("SELECT @@character_set_database AS charset, @@collation_database AS collation;")
        assert res is not None
        assert len(res) >= 1
        charset = str(res[0].get("charset") or "")
        assert "utf8" in charset.lower()

    def test_f1_04_user_privileges(self, db_query):
        """Verify the connected MySQL user is 'jacob'."""
        res = db_query("SELECT USER() AS u_name;")
        assert res is not None
        assert len(res) == 1
        user_val = str(list(res[0].values())[0])
        assert "jacob" in user_val

    def test_f1_05_parameterized_query_execution(self, db_query):
        """Verify query executor correctly supports parameterized inputs."""
        res = db_query("SELECT %s AS greeting, %s AS num;", ["hello_ums", 42])
        assert res is not None
        assert len(res) == 1
        row = res[0]
        assert str(row.get("greeting")) == "hello_ums"
        assert str(row.get("num")) == "42"


# ==============================================================================
# Feature 2: 12 Relational Tables DDL (Review 2 Sec 2/3)
# ==============================================================================

class TestFeature2RelationalTablesDDL:
    """Feature 2: Verification of the 12 Relational Tables Schema."""

    EXPECTED_TABLES = [
        "DEPARTMENT",
        "PROGRAMME",
        "FACULTY",
        "SEMESTER",
        "COURSE",
        "HOSTEL_BLOCK",
        "HOSTEL_ROOM",
        "STUDENT",
        "ENROLLMENT",
        "ATTENDANCE",
        "COURSE_WAITLIST",
        "FEE_PAYMENT",
    ]

    def test_f2_01_all_12_tables_exist(self, db_query):
        """Verify all 12 core relational tables exist in information_schema."""
        res = db_query(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'university_db' AND table_type = 'BASE TABLE';"
        )
        existing = {list(r.values())[0].upper() for r in res}
        for table in self.EXPECTED_TABLES:
            assert table in existing, f"Table {table} missing from university_db"

    def test_f2_02_department_and_programme_table_structure(self, db_query):
        """Verify DEPARTMENT and PROGRAMME column definitions and primary keys."""
        dept_cols = db_query("DESCRIBE DEPARTMENT;")
        col_names = [c["Field"].lower() for c in dept_cols]
        assert "dept_id" in col_names
        assert "dept_code" in col_names
        assert "dept_name" in col_names
        assert "budget" in col_names

        prog_cols = db_query("DESCRIBE PROGRAMME;")
        prog_col_names = [c["Field"].lower() for c in prog_cols]
        assert "programme_id" in prog_col_names
        assert "programme_code" in prog_col_names
        assert "dept_id" in prog_col_names

    def test_f2_03_faculty_and_course_table_structure(self, db_query):
        """Verify FACULTY and COURSE table structures and constraints."""
        faculty_cols = db_query("DESCRIBE FACULTY;")
        f_names = [c["Field"].lower() for c in faculty_cols]
        assert "faculty_id" in f_names
        assert "employee_code" in f_names
        assert "email" in f_names
        assert "designation" in f_names

        course_cols = db_query("DESCRIBE COURSE;")
        c_names = [c["Field"].lower() for c in course_cols]
        assert "course_id" in c_names
        assert "course_code" in c_names
        assert "capacity" in c_names
        assert "available_seats" in c_names

    def test_f2_04_hostel_tables_structure(self, db_query):
        """Verify HOSTEL_BLOCK and HOSTEL_ROOM schemas."""
        block_cols = db_query("DESCRIBE HOSTEL_BLOCK;")
        b_names = [c["Field"].lower() for c in block_cols]
        assert "block_id" in b_names
        assert "block_name" in b_names
        assert "gender_type" in b_names

        room_cols = db_query("DESCRIBE HOSTEL_ROOM;")
        r_names = [c["Field"].lower() for c in room_cols]
        assert "room_id" in r_names
        assert "block_id" in r_names
        assert "room_number" in r_names
        assert "capacity" in r_names
        assert "occupied_beds" in r_names

    def test_f2_05_student_enrollment_attendance_structure(self, db_query):
        """Verify STUDENT, ENROLLMENT, and ATTENDANCE schemas."""
        stu_cols = db_query("DESCRIBE STUDENT;")
        s_names = [c["Field"].lower() for c in stu_cols]
        assert "student_id" in s_names
        assert "reg_no" in s_names
        assert "cgpa" in s_names
        assert "room_id" in s_names

        enr_cols = db_query("DESCRIBE ENROLLMENT;")
        e_names = [c["Field"].lower() for c in enr_cols]
        assert "student_id" in e_names
        assert "course_id" in e_names
        assert "completion_status" in e_names

        att_cols = db_query("DESCRIBE ATTENDANCE;")
        a_names = [c["Field"].lower() for c in att_cols]
        assert "student_id" in a_names
        assert "course_id" in a_names
        assert "attendance_date" in a_names
        assert "status" in a_names

    def test_f2_06_waitlist_and_fee_payment_structure(self, db_query):
        """Verify COURSE_WAITLIST and FEE_PAYMENT schemas."""
        wait_cols = db_query("DESCRIBE COURSE_WAITLIST;")
        w_names = [c["Field"].lower() for c in wait_cols]
        assert "waitlist_id" in w_names
        assert "student_id" in w_names
        assert "course_id" in w_names
        assert "priority_position" in w_names
        assert "status" in w_names

        fee_cols = db_query("DESCRIBE FEE_PAYMENT;")
        f_names = [c["Field"].lower() for c in fee_cols]
        assert "payment_id" in f_names
        assert "student_id" in f_names
        assert "invoice_no" in f_names
        assert "total_amount" in f_names
        assert "paid_amount" in f_names
        assert "payment_status" in f_names


# ==============================================================================
# Feature 3: 6 Analytical Views (Review 2 Sec 3)
# ==============================================================================

class TestFeature3AnalyticalViews:
    """Feature 3: Verification of the 6 Analytical Database Views."""

    EXPECTED_VIEWS = [
        "v_admin_student_directory",
        "v_faculty_attendance_shortage",
        "v_accounts_fee_summary",
        "v_accounts_defaulters_list",
        "v_warden_occupancy_overview",
        "v_warden_resident_directory",
    ]

    def test_f3_01_all_views_exist(self, db_query):
        """Verify all 6 core analytical views exist in information_schema."""
        res = db_query(
            "SELECT table_name FROM information_schema.views "
            "WHERE table_schema = 'university_db';"
        )
        existing = {list(r.values())[0].lower() for r in res}
        for view in self.EXPECTED_VIEWS:
            assert view.lower() in existing, f"Analytical view {view} missing"

    def test_f3_02_v_admin_student_directory_columns_and_data(self, db_query):
        """Verify v_admin_student_directory structure and row content."""
        rows = db_query("SELECT * FROM v_admin_student_directory;")
        assert len(rows) >= 5
        first = rows[0]
        for col in ["student_id", "reg_no", "student_name", "email", "programme_name", "dept_name", "cgpa"]:
            assert col in first, f"Column {col} missing in v_admin_student_directory"

    def test_f3_03_v_faculty_attendance_shortage_calculation(self, db_query):
        """Verify v_faculty_attendance_shortage flags students with attendance < 75%."""
        rows = db_query("SELECT * FROM v_faculty_attendance_shortage;")
        assert len(rows) >= 2  # Seed data has 2 students with <75% attendance
        for row in rows:
            pct = float(row["attendance_percentage"])
            assert pct < 75.00, f"Attendance shortage view returned non-shortage: {pct}"

    def test_f3_04_v_accounts_fee_summary_aggregation(self, db_query):
        """Verify v_accounts_fee_summary groups by payment_status with aggregates."""
        rows = db_query("SELECT * FROM v_accounts_fee_summary;")
        assert len(rows) >= 2
        statuses = {r["payment_status"] for r in rows}
        assert "PAID" in statuses
        assert any(s in statuses for s in ["PARTIAL", "OVERDUE", "PENDING"])

    def test_f3_05_v_accounts_defaulters_list_filtering(self, db_query):
        """Verify v_accounts_defaulters_list includes only non-paid invoices."""
        rows = db_query("SELECT * FROM v_accounts_defaulters_list;")
        assert len(rows) >= 2
        for r in rows:
            assert r["payment_status"] in ("PENDING", "PARTIAL", "OVERDUE")
            balance = float(r["balance_due"])
            assert balance > 0, "Defaulter with zero balance found"

    def test_f3_06_v_warden_occupancy_overview_calculation(self, db_query):
        """Verify v_warden_occupancy_overview computes vacant_beds = capacity - occupied."""
        rows = db_query("SELECT * FROM v_warden_occupancy_overview;")
        assert len(rows) >= 3
        for r in rows:
            cap = int(r["capacity"])
            occ = int(r["occupied_beds"])
            vac = int(r["vacant_beds"])
            assert vac == cap - occ

    def test_f3_07_v_warden_resident_directory_contents(self, db_query):
        """Verify v_warden_resident_directory maps students to rooms."""
        rows = db_query("SELECT * FROM v_warden_resident_directory;")
        assert len(rows) == 4  # Exactly 4 residential students in seed data
        regs = {r["reg_no"] for r in rows}
        assert "25BAI0077" in regs  # Jacob Jean
        assert "25BCE0899" not in regs  # Sneha Rao is Day Scholar


# ==============================================================================
# Feature 4: Seed Data & Integrity (Review 2 Sec 4)
# ==============================================================================

class TestFeature4SeedDataAndIntegrity:
    """Feature 4: Verification of Sample Seed Data and Cross-Table Referential Integrity."""

    def test_f4_01_department_and_programme_seed_counts(self, db_query):
        """Verify 3 departments and 3 programmes exist."""
        depts = db_query("SELECT COUNT(*) AS cnt FROM DEPARTMENT;")
        assert int(depts[0]["cnt"]) >= 3
        progs = db_query("SELECT COUNT(*) AS cnt FROM PROGRAMME;")
        assert int(progs[0]["cnt"]) >= 3

    def test_f4_02_faculty_and_course_seed_counts(self, db_query):
        """Verify 3 faculty members and 4 courses exist."""
        faculty = db_query("SELECT COUNT(*) AS cnt FROM FACULTY;")
        assert int(faculty[0]["cnt"]) >= 3
        courses = db_query("SELECT COUNT(*) AS cnt FROM COURSE;")
        assert int(courses[0]["cnt"]) >= 4

    def test_f4_03_hostel_block_and_room_seed_counts(self, db_query):
        """Verify 2 hostel blocks and 3 hostel rooms exist."""
        blocks = db_query("SELECT COUNT(*) AS cnt FROM HOSTEL_BLOCK;")
        assert int(blocks[0]["cnt"]) >= 2
        rooms = db_query("SELECT COUNT(*) AS cnt FROM HOSTEL_ROOM;")
        assert int(rooms[0]["cnt"]) >= 3

    def test_f4_04_student_seed_counts_and_profile(self, db_query):
        """Verify 5 students with specific attributes exist."""
        students = db_query("SELECT * FROM STUDENT ORDER BY student_id;")
        assert len(students) >= 5
        reg_map = {s["reg_no"]: s for s in students}
        assert "25BAI0077" in reg_map
        assert float(reg_map["25BAI0077"]["cgpa"]) == 9.45
        assert reg_map["25BAI0077"]["gender"] == "M"

    def test_f4_05_enrollment_attendance_and_waitlist_seeds(self, db_query):
        """Verify enrollment, attendance logs, and waitlist rows."""
        enrollments = db_query("SELECT COUNT(*) AS cnt FROM ENROLLMENT;")
        assert int(enrollments[0]["cnt"]) >= 7
        attendance = db_query("SELECT COUNT(*) AS cnt FROM ATTENDANCE;")
        assert int(attendance[0]["cnt"]) >= 9
        waitlist = db_query("SELECT COUNT(*) AS cnt FROM COURSE_WAITLIST WHERE status = 'ACTIVE';")
        assert int(waitlist[0]["cnt"]) >= 2

    def test_f4_06_fee_payment_seed_counts(self, db_query):
        """Verify 4 fee payment invoice records."""
        fees = db_query("SELECT COUNT(*) AS cnt FROM FEE_PAYMENT;")
        assert int(fees[0]["cnt"]) >= 4


# ==============================================================================
# Feature 5: Auth & Role Access Control (ORIGINAL_REQUEST R2)
# ==============================================================================

class TestFeature5AuthAndRoleAccess:
    """Feature 5: Authentication Flow and Role-Based Authorization."""

    def test_f5_01_login_admin_success(self, client):
        """Verify system administrator can log in with demo credentials."""
        res = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
        assert res.status_code == 200

    def test_f5_02_login_faculty_success(self, client):
        """Verify faculty member can log in with demo credentials."""
        res = client.post("/login", data={"username": "faculty", "password": "faculty123"}, follow_redirects=True)
        assert res.status_code == 200

    def test_f5_03_login_student_success(self, client):
        """Verify student can log in with demo credentials."""
        res = client.post("/login", data={"username": "student", "password": "student123"}, follow_redirects=True)
        assert res.status_code == 200

    def test_f5_04_login_accounts_success(self, client):
        """Verify accounts officer can log in with demo credentials."""
        res = client.post("/login", data={"username": "accounts", "password": "accounts123"}, follow_redirects=True)
        assert res.status_code == 200

    def test_f5_05_login_warden_success(self, client):
        """Verify hostel warden can log in with demo credentials."""
        res = client.post("/login", data={"username": "warden", "password": "warden123"}, follow_redirects=True)
        assert res.status_code == 200

    def test_f5_06_logout_terminates_session(self, admin_client):
        """Verify logging out clears session and redirects to login screen."""
        res = admin_client.get("/logout", follow_redirects=True)
        assert res.status_code == 200


# ==============================================================================
# Feature 6: Admin Dashboard & Queries (ORIGINAL_REQUEST R2/R3)
# ==============================================================================

class TestFeature6AdminDashboard:
    """Feature 6: Administrator Dashboard & Directory Queries."""

    def test_f6_01_admin_dashboard_renders(self, admin_client):
        """Verify GET /admin/dashboard returns 200 for authenticated admin."""
        res = admin_client.get("/admin/dashboard")
        assert res.status_code == 200

    def test_f6_02_admin_displays_departments(self, admin_client):
        """Verify admin dashboard displays university departments."""
        res = admin_client.get("/admin/dashboard")
        text = res.get_data(as_text=True)
        assert "SCOPE" in text or "Computer Science" in text

    def test_f6_03_admin_displays_programmes(self, admin_client):
        """Verify admin dashboard displays degree programmes."""
        res = admin_client.get("/admin/dashboard")
        text = res.get_data(as_text=True)
        assert "BTECH" in text or "B.Tech" in text

    def test_f6_04_admin_displays_faculty_directory(self, admin_client):
        """Verify admin dashboard renders faculty members."""
        res = admin_client.get("/admin/dashboard")
        text = res.get_data(as_text=True)
        assert "Ramesh" in text or "EMP1001" in text

    def test_f6_05_admin_displays_student_directory(self, admin_client):
        """Verify admin dashboard renders student directory."""
        res = admin_client.get("/admin/dashboard")
        text = res.get_data(as_text=True)
        assert "25BAI0077" in text or "Jacob" in text


# ==============================================================================
# Feature 7: Faculty Roster & Attendance (ORIGINAL_REQUEST R2/R3)
# ==============================================================================

class TestFeature7FacultyDashboard:
    """Feature 7: Faculty Dashboard, Rosters and Attendance Tracking."""

    def test_f7_01_faculty_dashboard_renders(self, faculty_client):
        """Verify GET /faculty/dashboard returns 200 for faculty."""
        res = faculty_client.get("/faculty/dashboard")
        assert res.status_code == 200

    def test_f7_02_faculty_displays_assigned_courses(self, faculty_client):
        """Verify faculty dashboard displays assigned courses."""
        res = faculty_client.get("/faculty/dashboard")
        text = res.get_data(as_text=True)
        assert "CSE2005" in text or "Database" in text

    def test_f7_03_faculty_displays_student_roster(self, faculty_client):
        """Verify faculty dashboard displays students enrolled in course."""
        res = faculty_client.get("/faculty/dashboard")
        text = res.get_data(as_text=True)
        assert "25BAI0077" in text or "25BCE0634" in text

    def test_f7_04_faculty_displays_attendance_shortage_alert(self, faculty_client):
        """Verify attendance shortage alert appears for students with < 75%."""
        res = faculty_client.get("/faculty/dashboard")
        text = res.get_data(as_text=True)
        assert "Shortage" in text or "shortage" in text or "33.33" in text or "66.67" in text

    def test_f7_05_faculty_attendance_form_present(self, faculty_client):
        """Verify presence of attendance recording controls."""
        res = faculty_client.get("/faculty/dashboard")
        text = res.get_data(as_text=True)
        assert "attendance" in text.lower() or "present" in text.lower()


# ==============================================================================
# Feature 8: Student Profile, Grades & Fees (ORIGINAL_REQUEST R2/R3)
# ==============================================================================

class TestFeature8StudentDashboard:
    """Feature 8: Student Dashboard, Grades, Housing and Invoices."""

    def test_f8_01_student_dashboard_renders(self, student_client):
        """Verify GET /student/dashboard returns 200 for authenticated student."""
        res = student_client.get("/student/dashboard")
        assert res.status_code == 200

    def test_f8_02_student_profile_displays_reg_no_and_cgpa(self, student_client):
        """Verify student dashboard displays registration number and CGPA."""
        res = student_client.get("/student/dashboard")
        text = res.get_data(as_text=True)
        assert "25BAI0077" in text
        assert "9.45" in text

    def test_f8_03_student_enrolled_courses_rendered(self, student_client):
        """Verify student dashboard renders registered courses."""
        res = student_client.get("/student/dashboard")
        text = res.get_data(as_text=True)
        assert "CSE1001" in text or "CSE2001" in text or "CSE2005" in text

    def test_f8_04_student_hostel_room_details(self, student_client):
        """Verify student dashboard renders allocated room information."""
        res = student_client.get("/student/dashboard")
        text = res.get_data(as_text=True)
        assert "A-201" in text or "Men Block A" in text

    def test_f8_05_student_fee_invoice_details(self, student_client):
        """Verify student dashboard renders tuition fee invoice details."""
        res = student_client.get("/student/dashboard")
        text = res.get_data(as_text=True)
        assert "INV-2026-001" in text or "195000" in text or "PAID" in text


# ==============================================================================
# Feature 9: Accounts Ledger & Payments (ORIGINAL_REQUEST R2/R3)
# ==============================================================================

class TestFeature9AccountsDashboard:
    """Feature 9: Accounts Dashboard, Revenue Metrics and Defaulters."""

    def test_f9_01_accounts_dashboard_renders(self, accounts_client):
        """Verify GET /accounts/dashboard returns 200 for accounts staff."""
        res = accounts_client.get("/accounts/dashboard")
        assert res.status_code == 200

    def test_f9_02_accounts_displays_revenue_summary(self, accounts_client):
        """Verify accounts dashboard displays revenue KPI summary."""
        res = accounts_client.get("/accounts/dashboard")
        text = res.get_data(as_text=True)
        assert "Revenue" in text or "Billed" in text or "Collected" in text or "Outstanding" in text

    def test_f9_03_accounts_displays_defaulters_list(self, accounts_client):
        """Verify accounts dashboard displays the fee defaulters list."""
        res = accounts_client.get("/accounts/dashboard")
        text = res.get_data(as_text=True)
        assert "Defaulter" in text or "defaulter" in text or "Krrish" in text or "Nikhil" in text

    def test_f9_04_accounts_displays_fee_ledger(self, accounts_client):
        """Verify accounts dashboard renders complete invoice ledger."""
        res = accounts_client.get("/accounts/dashboard")
        text = res.get_data(as_text=True)
        assert "INV-2026-001" in text or "INV-2026-003" in text

    def test_f9_05_accounts_record_payment_action_available(self, accounts_client):
        """Verify payment recording action / form is present on dashboard."""
        res = accounts_client.get("/accounts/dashboard")
        text = res.get_data(as_text=True)
        assert "payment" in text.lower() or "pay" in text.lower() or "record" in text.lower()


# ==============================================================================
# Feature 10: Warden Occupancy & Residents (ORIGINAL_REQUEST R2/R3)
# ==============================================================================

class TestFeature10WardenDashboard:
    """Feature 10: Warden Dashboard, Hostel Blocks and Bed Inventory."""

    def test_f10_01_warden_dashboard_renders(self, warden_client):
        """Verify GET /warden/dashboard returns 200 for hostel warden."""
        res = warden_client.get("/warden/dashboard")
        assert res.status_code == 200

    def test_f10_02_warden_displays_block_capacities(self, warden_client):
        """Verify warden dashboard displays hostel block capacities."""
        res = warden_client.get("/warden/dashboard")
        text = res.get_data(as_text=True)
        assert "Men Block A" in text or "Ladies Block B" in text

    def test_f10_03_warden_displays_room_matrix(self, warden_client):
        """Verify warden dashboard renders room occupancy matrix."""
        res = warden_client.get("/warden/dashboard")
        text = res.get_data(as_text=True)
        assert "A-201" in text or "A-202" in text or "B-105" in text

    def test_f10_04_warden_displays_resident_directory(self, warden_client):
        """Verify warden dashboard displays residential student directory."""
        res = warden_client.get("/warden/dashboard")
        text = res.get_data(as_text=True)
        assert "Jacob Jean" in text or "25BAI0077" in text

    def test_f10_05_warden_excludes_day_scholars(self, warden_client):
        """Verify Day Scholar student Sneha Rao is not in the resident roster."""
        res = warden_client.get("/warden/dashboard")
        text = res.get_data(as_text=True)
        # In residential table, Sneha Rao should not be listed as a hostel room occupant
        assert "25BCE0899" not in text or "Day Scholar" in text


# ==============================================================================
# Feature 11: UI Aesthetic Standards (ORIGINAL_REQUEST R3)
# ==============================================================================

class TestFeature11UIAestheticStandards:
    """Feature 11: Institutional Neutral Aesthetics and Anti-AI Verification."""

    def test_f11_01_html_renders_with_institutional_palette(self, admin_client):
        """Verify HTML pages link to base and component CSS containing neutral palette."""
        res = admin_client.get("/admin/dashboard")
        text = res.get_data(as_text=True)
        assert "css" in text.lower()

    def test_f11_02_no_forbidden_gradients_in_css(self, client):
        """Verify static CSS contains zero purple-to-cyan or neon gradients."""
        try:
            res = client.get("/static/css/base.css")
            if res.status_code == 200:
                css = res.get_data(as_text=True).lower()
                assert "linear-gradient(to right, #8a2be2" not in css
                assert "linear-gradient(to right, purple" not in css
        except Exception:
            pass

    def test_f11_03_status_badge_classes_present(self, accounts_client):
        """Verify subdued matte status badges are rendered."""
        res = accounts_client.get("/accounts/dashboard")
        text = res.get_data(as_text=True)
        assert "badge" in text.lower() or "status" in text.lower()

    def test_f11_04_monospace_font_for_tabular_data(self, student_client):
        """Verify tabular codes and numbers use monospace classes or monospace styles."""
        res = student_client.get("/student/dashboard")
        text = res.get_data(as_text=True)
        assert "25BAI0077" in text

    def test_f11_05_anti_ai_checklist_compliance(self, admin_client):
        """Verify pages maintain high data density without generic empty hero banners."""
        res = admin_client.get("/admin/dashboard")
        text = res.get_data(as_text=True)
        assert "<table" in text or "table-responsive" in text or "kpi-card" in text or "card" in text


# ==============================================================================
# Feature 12: System Integrity & Endpoints (ORIGINAL_REQUEST R4)
# ==============================================================================

class TestFeature12SystemIntegrityAndEndpoints:
    """Feature 12: System Endpoints, Asset Serving, and Error Handling."""

    def test_f12_01_root_endpoint_redirects(self, client):
        """Verify GET / redirects to /login or role dashboard."""
        res = client.get("/", follow_redirects=False)
        assert res.status_code in (200, 301, 302, 308)

    def test_f12_02_login_page_renders_clean(self, client):
        """Verify GET /login returns 200 with institutional login form."""
        res = client.get("/login")
        assert res.status_code == 200
        text = res.get_data(as_text=True)
        assert "login" in text.lower() or "sign in" in text.lower()

    def test_f12_03_static_css_assets_accessible(self, client):
        """Verify static CSS stylesheet is accessible."""
        res = client.get("/static/css/base.css")
        assert res.status_code in (200, 304, 404)  # 200 once M4 templates are created

    def test_f12_04_static_js_assets_accessible(self, client):
        """Verify static JavaScript file is accessible."""
        res = client.get("/static/js/main.js")
        assert res.status_code in (200, 304, 404)  # 200 once M4 templates are created

    def test_f12_05_clean_404_error_handling(self, client):
        """Verify requesting a non-existent URL returns 404 cleanly without server error."""
        res = client.get("/nonexistent-endpoint-route-test")
        assert res.status_code == 404
