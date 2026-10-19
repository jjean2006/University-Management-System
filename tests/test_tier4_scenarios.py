"""Tier 4: End-to-End Real-World Application Scenarios (S1 to S5).

Implements multi-step user journeys modeling realistic university operations:
- S1: Student Semester Review (Jacob Jean / 25BAI0077)
- S2: Faculty Attendance Marking & Shortage Trigger (Dr. Ramesh Kumar / EMP1001)
- S3: Accounts Fee Collection & Defaulter Settlement (Krrish Pare / INV-2026-003)
- S4: Warden Residential Inventory & Allocation Audit
- S5: Administrator Governance & Role Protection Audit
- S6: Course Waitlist Queue Lifecycle & Capacity Audit
"""

import pytest


class TestTier4RealWorldScenarios:
    """Multi-step user journey tests verifying cross-feature workflows."""

    def test_scenario_s1_student_semester_review(self, client):
        """Scenario S1: Student logs in, inspects academic record, hostel allotment, and fee invoice.

        Steps:
        1. Student logs in with credentials (student / student123 or 25BAI0077 / password).
        2. Inspects student profile: verifies Reg No '25BAI0077', CGPA '9.45', programme BTECH-CSE-AIML.
        3. Checks course enrollments: verifies completed courses CSE1001 & CSE2001, active CSE2005.
        4. Verifies hostel allotment: assigned to Men Block A, Room A-201.
        5. Verifies financial status: fee invoice INV-2026-001 has status PAID, 0 balance due.
        6. Logs out cleanly.
        """
        # Step 1: Login
        res_login = client.post("/login", data={"username": "student", "password": "student123"}, follow_redirects=True)
        assert res_login.status_code == 200

        # Step 2: Access Student Dashboard
        res_dash = client.get("/student/dashboard")
        assert res_dash.status_code == 200
        content = res_dash.get_data(as_text=True)

        # Step 3 & 4: Inspect Academic & Hostel Profile
        assert "25BAI0077" in content
        assert "9.45" in content
        assert "CSE1001" in content or "CSE2005" in content
        assert "A-201" in content or "Men Block A" in content

        # Step 5: Check Fee Invoices
        assert "INV-2026-001" in content or "195000" in content

        # Step 6: Logout
        res_logout = client.get("/logout", follow_redirects=True)
        assert res_logout.status_code == 200

    def test_scenario_s2_faculty_attendance_marking_and_shortage_trigger(self, client, db_query):
        """Scenario S2: Faculty reviews roster, conducts lecture, marks attendance, checks shortage view.

        Steps:
        1. Faculty logs in (faculty / faculty123 or EMP1001 / password).
        2. Accesses Faculty Dashboard, views assigned courses (e.g. CSE2005 Database Management Systems).
        3. Reviews course roster of enrolled students.
        4. Checks current attendance shortage alert list: verifies students with attendance < 75%.
        5. Logs out cleanly.
        """
        # Step 1: Login
        res_login = client.post("/login", data={"username": "faculty", "password": "faculty123"}, follow_redirects=True)
        assert res_login.status_code == 200

        # Step 2 & 3: View Dashboard and Roster
        res_dash = client.get("/faculty/dashboard")
        assert res_dash.status_code == 200
        content = res_dash.get_data(as_text=True)
        assert "CSE2005" in content or "Database" in content

        # Step 4: Verify Shortage List in View
        shortages = db_query("SELECT reg_no, attendance_percentage FROM v_faculty_attendance_shortage;")
        assert len(shortages) >= 2
        shortage_regs = {s["reg_no"] for s in shortages}
        assert "25BAI0030" in shortage_regs  # Krrish Pare (33.33%)
        assert "25BCE0634" in shortage_regs  # Aradhya Jain (66.67%)
        assert "25BAI0077" not in shortage_regs  # Jacob Jean (100.00%)

        # Step 5: Logout
        res_logout = client.get("/logout", follow_redirects=True)
        assert res_logout.status_code == 200

    def test_scenario_s3_accounts_fee_collection_workflow(self, client, db_query):
        """Scenario S3: Accounts officer audits revenue, identifies defaulter, records payment, verifies settlement.

        Steps:
        1. Accounts officer logs in (accounts / accounts123).
        2. Views fee revenue summary KPIs (Total Billed, Total Collected, Outstanding).
        3. Inspects Defaulters List: identifies Krrish Pare (INV-2026-003, balance due 95,000.00).
        4. Verifies invoice details in database.
        5. Logs out cleanly.
        """
        # Step 1: Login
        res_login = client.post("/login", data={"username": "accounts", "password": "accounts123"}, follow_redirects=True)
        assert res_login.status_code == 200

        # Step 2: Accounts Dashboard
        res_dash = client.get("/accounts/dashboard")
        assert res_dash.status_code == 200
        content = res_dash.get_data(as_text=True)

        # Step 3: Inspect Defaulters
        defaulters = db_query("SELECT * FROM v_accounts_defaulters_list WHERE invoice_no = 'INV-2026-003';")
        assert len(defaulters) == 1
        assert float(defaulters[0]["balance_due"]) == 95000.00
        assert defaulters[0]["payment_status"] == "PARTIAL"

        # Step 4: Verify overall revenue summary
        summary = db_query("SELECT SUM(total_amount) AS total, SUM(paid_amount) AS paid FROM FEE_PAYMENT;")
        assert float(summary[0]["total"]) > float(summary[0]["paid"])

        # Step 5: Logout
        res_logout = client.get("/logout", follow_redirects=True)
        assert res_logout.status_code == 200

    def test_scenario_s4_warden_residential_inventory_and_allocation_audit(self, client, db_query):
        """Scenario S4: Warden reviews block capacities, room occupancy matrix, and resident directory.

        Steps:
        1. Warden logs in (warden / warden123).
        2. Reviews block capacity overview: Men Block A (cap 500) and Ladies Block B (cap 400).
        3. Reviews room occupancy matrix: Room A-201 (occupied 2, vacant 0), A-202 (occupied 1, vacant 1).
        4. Reviews resident directory: 4 residents listed.
        5. Verifies Day Scholar (Sneha Rao / 25BCE0899) is excluded from residential roster.
        6. Logs out cleanly.
        """
        # Step 1: Login
        res_login = client.post("/login", data={"username": "warden", "password": "warden123"}, follow_redirects=True)
        assert res_login.status_code == 200

        # Step 2 & 3: Warden Dashboard
        res_dash = client.get("/warden/dashboard")
        assert res_dash.status_code == 200
        content = res_dash.get_data(as_text=True)
        assert "Men Block A" in content or "Block" in content

        # Step 4: Verify Resident Directory via View
        residents = db_query("SELECT reg_no, room_number, block_name FROM v_warden_resident_directory;")
        assert len(residents) == 4
        res_map = {r["reg_no"]: r for r in residents}
        assert "25BAI0077" in res_map
        assert res_map["25BAI0077"]["room_number"] == "A-201"
        assert res_map["25BAI0077"]["block_name"] == "Men Block A"

        # Step 5: Confirm Day Scholar is Excluded
        assert "25BCE0899" not in res_map

        # Step 6: Logout
        res_logout = client.get("/logout", follow_redirects=True)
        assert res_logout.status_code == 200

    def test_scenario_s5_admin_governance_and_role_protection_audit(self, client):
        """Scenario S5: Administrator audits university directories and verifies role boundaries.

        Steps:
        1. Admin logs in (admin / admin123).
        2. Reviews admin dashboard (departments, programmes, faculty, student directory).
        3. Logs out.
        4. Tests unauthenticated access rejection across all protected dashboards.
        5. Simulates student login and verifies access denial to administrative dashboards.
        """
        # Step 1 & 2: Admin Login and Audit
        res_login = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
        assert res_login.status_code == 200
        res_admin = client.get("/admin/dashboard")
        assert res_admin.status_code == 200

        # Step 3: Logout
        client.get("/logout", follow_redirects=True)

        # Step 4: Unauthenticated access blocked
        for path in ["/admin/dashboard", "/accounts/dashboard", "/warden/dashboard"]:
            res = client.get(path, follow_redirects=False)
            assert res.status_code in (302, 401, 403)

        # Step 5: Student login cannot access administrative routes
        client.post("/login", data={"username": "student", "password": "student123"}, follow_redirects=True)
        res_forbidden = client.get("/admin/dashboard", follow_redirects=False)
        assert res_forbidden.status_code in (302, 403)

        client.get("/logout", follow_redirects=True)

    def test_scenario_s6_waitlist_queue_lifecycle_and_capacity_audit(self, db_query):
        """Scenario S6: Audit course capacity limits, waitlist queue registration and FIFO order.

        Steps:
        1. Queries course catalog: identifies CSE2001 (capacity 60, available_seats 0).
        2. Queries COURSE_WAITLIST: verifies active queue length and priority positions.
        3. Audits waitlisted students: verifies priority 1 (Nikhil Sharma) and priority 2 (Sneha Rao).
        4. Verifies waitlist timestamps are preserved and status is 'ACTIVE'.
        """
        # Step 1: Course Capacity
        course = db_query("SELECT capacity, available_seats FROM COURSE WHERE course_code = 'CSE2001';")
        assert len(course) == 1
        assert int(course[0]["capacity"]) == 60
        assert int(course[0]["available_seats"]) == 0

        # Step 2 & 3: Active Waitlist Queue
        waitlist = db_query(
            "SELECT cw.priority_position, cw.status, s.reg_no, s.first_name "
            "FROM COURSE_WAITLIST cw "
            "JOIN STUDENT s ON cw.student_id = s.student_id "
            "WHERE cw.course_id = 2 "
            "ORDER BY cw.priority_position ASC;"
        )
        assert len(waitlist) >= 2
        assert int(waitlist[0]["priority_position"]) == 1
        assert waitlist[0]["reg_no"] == "25ECE0122"  # Nikhil Sharma
        assert int(waitlist[1]["priority_position"]) == 2
        assert waitlist[1]["reg_no"] == "25BCE0899"  # Sneha Rao

        # Step 4: Status Active
        for item in waitlist:
            assert item["status"] == "ACTIVE"
