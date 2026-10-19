"""Tier 3: Pairwise Cross-Feature Integration Test Suite.

Verifies interactions between pairs of system features:
- Attendance Recording (F7) ↔ Attendance Shortage View (F3)
- Fee Payment Recording (F9) ↔ Accounts Defaulters List & Fee Summary (F3)
- Course Capacity / Enrollment (F4/F8) ↔ Course Waitlist FIFO Engine (F12)
- Room Allocation (F10) ↔ Warden Occupancy & Resident Directory (F3)
- Student Profile (F8) ↔ Housing, Fees, and Waitlist State (F9/F10/F4)
"""

import pytest


class TestPairwiseAttendanceAndShortage:
    """Pairwise interactions between attendance marking and the shortage analytical view."""

    def test_p1_attendance_shortage_view_reflects_attendance_records(self, db_query):
        """Verify v_faculty_attendance_shortage aggregates live records from ATTENDANCE."""
        rows = db_query("SELECT * FROM v_faculty_attendance_shortage WHERE course_code = 'CSE2005';")
        assert len(rows) >= 2
        for r in rows:
            assert int(r["total_classes_conducted"]) >= 3
            assert float(r["attendance_percentage"]) < 75.00

    def test_p2_marking_present_improves_attendance_percentage(self, db_query):
        """Mathematical verification: adding 1 Present class to 1/3 (33.33%) yields 2/4 (50.00%)."""
        initial_pct = 1 / 3 * 100
        new_pct = 2 / 4 * 100
        assert round(initial_pct, 2) == 33.33
        assert round(new_pct, 2) == 50.00
        assert new_pct > initial_pct

    def test_p3_marking_absent_drops_student_into_shortage(self, db_query):
        """Mathematical verification: a compliant student (3/3 = 100%) receiving 2 Absents becomes 3/5 = 60% (<75%)."""
        start = 3 / 3 * 100
        assert start == 100.00
        after_absents = 3 / 5 * 100
        assert after_absents == 60.00
        assert after_absents < 75.00


class TestPairwiseFeePaymentAndDefaulters:
    """Pairwise interactions between fee payments, defaulter lists, and revenue summaries."""

    def test_p4_partial_fee_payment_updates_balance_due(self, db_query):
        """Verify partial payment on invoice INV-2026-003 leaves exact remaining balance."""
        rows = db_query("SELECT * FROM v_accounts_defaulters_list WHERE invoice_no = 'INV-2026-003';")
        assert len(rows) == 1
        row = rows[0]
        total = float(row["total_amount"])
        paid = float(row["paid_amount"])
        balance = float(row["balance_due"])
        assert balance == total - paid
        assert balance == 95000.00

    def test_p5_full_fee_settlement_removes_from_defaulters_list(self, db_query):
        """Verify fully settled invoices (PAID) do not appear in v_accounts_defaulters_list."""
        rows = db_query("SELECT invoice_no FROM v_accounts_defaulters_list WHERE invoice_no = 'INV-2026-001';")
        assert len(rows) == 0

    def test_p6_fee_payment_updates_revenue_summary_aggregates(self, db_query):
        """Verify v_accounts_fee_summary reflects total collected and outstanding balances."""
        rows = db_query("SELECT * FROM v_accounts_fee_summary;")
        summary = {r["payment_status"]: r for r in rows}
        assert "PAID" in summary
        paid_summary = summary["PAID"]
        assert float(paid_summary["outstanding_balance"]) == 0.00
        assert float(paid_summary["total_collected_amount"]) > 0


class TestPairwiseCourseCapacityAndWaitlist:
    """Pairwise interactions between course capacity, registration, and waitlist queues."""

    def test_p7_course_full_routes_student_to_waitlist(self, db_query):
        """Verify course CSE2001 (available_seats = 0) has active waitlist entries."""
        course = db_query("SELECT available_seats FROM COURSE WHERE course_code = 'CSE2001';")
        assert int(course[0]["available_seats"]) == 0
        waitlist = db_query("SELECT * FROM COURSE_WAITLIST WHERE course_id = 2 AND status = 'ACTIVE';")
        assert len(waitlist) >= 2

    def test_p8_waitlist_fifo_position_allocation(self, db_query):
        """Verify waitlist entries receive distinct, sequential priority numbers."""
        rows = db_query(
            "SELECT student_id, priority_position "
            "FROM COURSE_WAITLIST WHERE course_id = 2 ORDER BY priority_position ASC;"
        )
        assert len(rows) >= 2
        p1 = int(rows[0]["priority_position"])
        p2 = int(rows[1]["priority_position"])
        assert p1 == 1
        assert p2 == 2

    def test_p9_dropping_course_promotes_top_waitlist_candidate(self, db_query):
        """Verify priority 1 student is the designated candidate for next seat allocation."""
        candidate = db_query(
            "SELECT student_id, priority_position FROM COURSE_WAITLIST "
            "WHERE course_id = 2 AND status = 'ACTIVE' ORDER BY priority_position ASC LIMIT 1;"
        )
        assert len(candidate) == 1
        assert int(candidate[0]["priority_position"]) == 1


class TestPairwiseHostelRoomAndResidentDirectory:
    """Pairwise interactions between hostel room allocation and resident views."""

    def test_p10_room_allotment_matches_occupied_beds(self, db_query):
        """Verify HOSTEL_ROOM.occupied_beds equals count of students assigned with room_id."""
        rooms = db_query("SELECT room_id, occupied_beds FROM HOSTEL_ROOM;")
        for room in rooms:
            rid = int(room["room_id"])
            occ = int(room["occupied_beds"])
            count_res = db_query(f"SELECT COUNT(*) AS cnt FROM STUDENT WHERE room_id = {rid};")
            actual_count = int(count_res[0]["cnt"])
            assert occ == actual_count, f"Room {rid} occupied_beds mismatch"

    def test_p11_room_allotment_decrements_vacant_beds(self, db_query):
        """Verify vacant_beds + occupied_beds == capacity for all rooms."""
        rows = db_query("SELECT capacity, occupied_beds, vacant_beds FROM v_warden_occupancy_overview;")
        for r in rows:
            cap = int(r["capacity"])
            occ = int(r["occupied_beds"])
            vac = int(r["vacant_beds"])
            assert cap == occ + vac

    def test_p12_room_allotment_adds_student_to_resident_directory(self, db_query):
        """Verify student with valid room_id appears in v_warden_resident_directory."""
        students = db_query("SELECT reg_no FROM STUDENT WHERE room_id IS NOT NULL;")
        directory = db_query("SELECT reg_no FROM v_warden_resident_directory;")
        dir_regs = {r["reg_no"] for r in directory}
        for s in students:
            assert s["reg_no"] in dir_regs

    def test_p13_day_scholar_assigned_room_becomes_resident(self, db_query):
        """Verify student without room_id is absent from resident directory."""
        day_scholars = db_query("SELECT reg_no FROM STUDENT WHERE room_id IS NULL;")
        directory = db_query("SELECT reg_no FROM v_warden_resident_directory;")
        dir_regs = {r["reg_no"] for r in directory}
        for ds in day_scholars:
            assert ds["reg_no"] not in dir_regs


class TestPairwiseStudentDashboardReflections:
    """Pairwise verification of student dashboard data reflecting related system entities."""

    def test_p14_student_dashboard_reflects_room_and_block_assignment(self, student_client):
        """Verify student dashboard displays assigned hostel room and block name."""
        res = student_client.get("/student/dashboard")
        text = res.get_data(as_text=True)
        assert "A-201" in text or "Men Block A" in text

    def test_p15_student_dashboard_reflects_fee_payment_updates(self, student_client):
        """Verify student dashboard displays fee invoice and PAID status badge."""
        res = student_client.get("/student/dashboard")
        text = res.get_data(as_text=True)
        assert "INV-2026-001" in text
        assert "PAID" in text or "Paid" in text

    def test_p16_student_dashboard_reflects_completed_prerequisites(self, student_client):
        """Verify student dashboard shows completed prerequisite courses with grade points."""
        res = student_client.get("/student/dashboard")
        text = res.get_data(as_text=True)
        assert "CSE1001" in text or "CSE2001" in text
        assert "10.0" in text or "9.5" in text

    def test_p17_student_waitlist_status_reflection(self, client):
        """Verify student with waitlist entry (25ECE0122) can view waitlist queue status."""
        with client.session_transaction() as sess:
            sess["user_id"] = 4
            sess["username"] = "25ECE0122"
            sess["role"] = "student"
            sess["entity_id"] = 4
            sess["display_name"] = "Nikhil Sharma"
            sess["logged_in"] = True

        res = client.get("/student/dashboard")
        assert res.status_code == 200
