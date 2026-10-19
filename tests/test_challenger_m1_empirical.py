"""Empirical Challenger Test Suite for Milestone 1 Database Integrity & Connection Resilience.

Tests:
1. Foreign Key Constraints (RESTRICT, CASCADE, SET NULL, invalid parent references).
2. Unique Key Constraints (email, reg_no, course_code, emp_code, dept_code, programme_code, block_room, invoice_no).
3. Primary Key & Composite Key Integrity (ENROLLMENT, ATTENDANCE).
4. Connection Resilience & Socket/Port Fallback Behavior in app/db.py.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.config import Config
from app.db import get_db_connection, execute_query, MySQLCLIConnection, _try_pymysql

def run_sql_raw(sql):
    """Run a multi-statement SQL script on the configured database.

    Returns (returncode, stdout, stderr) in the same shape as the mysql CLI in batch
    mode: result sets as tab-separated text, errors as 'ERROR <code>: <message>'.
    """
    conn = _try_pymysql(multi_statements=True)
    assert conn is not None, "Could not connect to MySQL with the configured credentials"
    out_lines = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            while True:
                if cur.description:
                    out_lines.append("\t".join(d[0] for d in cur.description))
                    for row in cur.fetchall():
                        out_lines.append("\t".join("NULL" if v is None else str(v) for v in row.values()))
                if not cur.nextset():
                    break
        return 0, "\n".join(out_lines) + "\n", ""
    except Exception as e:
        code = e.args[0] if e.args else ""
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return 1, "\n".join(out_lines), f"ERROR {code}: {msg}"
    finally:
        conn.close()  # closing discards any open transaction


def test_fk_nonexistent_programme_fails():
    """Attempt to insert student with non-existent programme_id (9999). Must fail with error 1452."""
    sql = """
    START TRANSACTION;
    INSERT INTO STUDENT (reg_no, first_name, last_name, email, dob, gender, cgpa, programme_id)
    VALUES ('TEST999', 'Fake', 'Student', 'fake@univ.ac.in', '2005-01-01', 'M', 8.0, 9999);
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "FK violation should have failed but succeeded!"
    assert "1452" in err or "foreign key constraint fails" in err.lower()
    return True, "Properly rejected with MySQL 1452 foreign key error"


def test_fk_nonexistent_advisor_fails():
    """Attempt to insert student with non-existent advisor_id (9999). Must fail with error 1452."""
    sql = """
    START TRANSACTION;
    INSERT INTO STUDENT (reg_no, first_name, last_name, email, dob, gender, cgpa, programme_id, advisor_id)
    VALUES ('TEST998', 'Fake', 'AdvisorStudent', 'fake_adv@univ.ac.in', '2005-01-01', 'M', 8.0, 1, 9999);
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "FK violation should have failed but succeeded!"
    assert "1452" in err or "foreign key constraint fails" in err.lower()
    return True, "Properly rejected with MySQL 1452 foreign key error"


def test_fk_nonexistent_room_fails():
    """Attempt to insert student with non-existent room_id (9999). Must fail with error 1452."""
    sql = """
    START TRANSACTION;
    INSERT INTO STUDENT (reg_no, first_name, last_name, email, dob, gender, cgpa, programme_id, room_id)
    VALUES ('TEST997', 'Fake', 'RoomStudent', 'fake_room@univ.ac.in', '2005-01-01', 'M', 8.0, 1, 9999);
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "FK violation should have failed but succeeded!"
    assert "1452" in err or "foreign key constraint fails" in err.lower()
    return True, "Properly rejected with MySQL 1452 foreign key error"


def test_fk_delete_dept_restrict_fails():
    """Attempt to delete department referenced by programme/faculty/course. Must fail with error 1451."""
    sql = """
    START TRANSACTION;
    DELETE FROM DEPARTMENT WHERE dept_id = 1;
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "Deleting department with active references should fail!"
    assert "1451" in err or "foreign key constraint fails" in err.lower()
    return True, "Properly rejected with MySQL 1451 RESTRICT error"


def test_fk_delete_programme_restrict_fails():
    """Attempt to delete programme referenced by student. Must fail with error 1451."""
    sql = """
    START TRANSACTION;
    DELETE FROM PROGRAMME WHERE programme_id = 1;
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "Deleting programme with active students should fail!"
    assert "1451" in err or "foreign key constraint fails" in err.lower()
    return True, "Properly rejected with MySQL 1451 RESTRICT error"


def test_fk_delete_semester_restrict_fails():
    """Attempt to delete semester referenced by active enrollment. Must fail with error 1451."""
    sql = """
    START TRANSACTION;
    DELETE FROM SEMESTER WHERE semester_id = 1;
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "Deleting semester with active enrollments should fail!"
    assert "1451" in err or "foreign key constraint fails" in err.lower()
    return True, "Properly rejected with MySQL 1451 RESTRICT error"


def test_fk_delete_room_sets_student_room_null():
    """Verify ON DELETE SET NULL on student room_id when room is deleted."""
    sql = """
    START TRANSACTION;
    -- Create temporary block, room, and student
    INSERT INTO HOSTEL_BLOCK (block_name, gender_type, total_capacity) VALUES ('Temp Block', 'M', 10);
    SET @b_id = LAST_INSERT_ID();
    INSERT INTO HOSTEL_ROOM (block_id, room_number, floor_number, capacity, monthly_rent)
    VALUES (@b_id, 'T-101', 1, 2, 5000.00);
    SET @r_id = LAST_INSERT_ID();
    INSERT INTO STUDENT (reg_no, first_name, last_name, email, dob, gender, cgpa, programme_id, room_id)
    VALUES ('TEST_NULL', 'Temp', 'Resident', 'temp_res@univ.ac.in', '2005-01-01', 'M', 7.5, 1, @r_id);
    SET @s_id = LAST_INSERT_ID();

    -- Delete room
    DELETE FROM HOSTEL_ROOM WHERE room_id = @r_id;

    -- Verify student room_id became NULL
    SELECT room_id FROM STUDENT WHERE student_id = @s_id;
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code == 0, f"Failed executing query: {err}"
    lines = [line.strip() for line in out.split("\n") if line.strip()]
    assert "NULL" in lines[-1], f"Expected room_id to become NULL, got: {out}"
    return True, "ON DELETE SET NULL successfully set room_id to NULL"


def test_fk_delete_student_cascades_to_enrollment_and_fees():
    """Verify ON DELETE CASCADE when student is deleted: enrollments, attendance, waitlist, fee payments cascade."""
    sql = """
    START TRANSACTION;
    INSERT INTO STUDENT (reg_no, first_name, last_name, email, dob, gender, cgpa, programme_id)
    VALUES ('TEST_CAS', 'Temp', 'Cascade', 'temp_cas@univ.ac.in', '2005-01-01', 'M', 7.5, 1);
    SET @s_id = LAST_INSERT_ID();
    INSERT INTO ENROLLMENT (student_id, course_id, semester_id, enrollment_date)
    VALUES (@s_id, 1, 1, '2026-01-10');
    INSERT INTO FEE_PAYMENT (student_id, invoice_no, total_amount, due_date)
    VALUES (@s_id, 'INV-TEST-CAS', 100000.00, '2026-03-01');

    DELETE FROM STUDENT WHERE student_id = @s_id;

    SELECT COUNT(*) FROM ENROLLMENT WHERE student_id = @s_id;
    SELECT COUNT(*) FROM FEE_PAYMENT WHERE student_id = @s_id;
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code == 0, f"Failed executing query: {err}"
    assert "0" in out
    return True, "ON DELETE CASCADE successfully pruned child records across tables"


def test_unique_duplicate_student_email_fails():
    """Attempt to insert student with duplicate email (jacob.jean2025@vitstudent.ac.in). Must fail with 1062."""
    sql = """
    START TRANSACTION;
    INSERT INTO STUDENT (reg_no, first_name, last_name, email, dob, gender, cgpa, programme_id)
    VALUES ('TEST_DUP1', 'Dup', 'Email', 'jacob.jean2025@vitstudent.ac.in', '2005-01-01', 'M', 8.0, 1);
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "Duplicate student email should have failed!"
    assert "1062" in err or "duplicate entry" in err.lower()
    return True, "Properly rejected with MySQL 1062 duplicate entry error"


def test_unique_duplicate_student_reg_no_fails():
    """Attempt to insert student with duplicate reg_no (25BAI0077). Must fail with 1062."""
    sql = """
    START TRANSACTION;
    INSERT INTO STUDENT (reg_no, first_name, last_name, email, dob, gender, cgpa, programme_id)
    VALUES ('25BAI0077', 'Dup', 'RegNo', 'unique_email@univ.ac.in', '2005-01-01', 'M', 8.0, 1);
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "Duplicate student reg_no should have failed!"
    assert "1062" in err or "duplicate entry" in err.lower()
    return True, "Properly rejected with MySQL 1062 duplicate entry error"


def test_unique_duplicate_course_code_fails():
    """Attempt to insert course with duplicate course_code (CSE1001). Must fail with 1062."""
    sql = """
    START TRANSACTION;
    INSERT INTO COURSE (course_code, course_title, credits, capacity, available_seats, dept_id)
    VALUES ('CSE1001', 'Duplicate Course', 3, 60, 60, 1);
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "Duplicate course_code should have failed!"
    assert "1062" in err or "duplicate entry" in err.lower()
    return True, "Properly rejected with MySQL 1062 duplicate entry error"


def test_unique_duplicate_faculty_email_fails():
    """Attempt to insert faculty with duplicate email (ramesh.kumar@vit.ac.in). Must fail with 1062."""
    sql = """
    START TRANSACTION;
    INSERT INTO FACULTY (employee_code, first_name, last_name, email, phone, designation, dept_id)
    VALUES ('EMP9999', 'Fake', 'Faculty', 'ramesh.kumar@vit.ac.in', '9999999999', 'Professor', 1);
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "Duplicate faculty email should have failed!"
    assert "1062" in err or "duplicate entry" in err.lower()
    return True, "Properly rejected with MySQL 1062 duplicate entry error"


def test_unique_duplicate_faculty_emp_code_fails():
    """Attempt to insert faculty with duplicate employee_code (EMP1001). Must fail with 1062."""
    sql = """
    START TRANSACTION;
    INSERT INTO FACULTY (employee_code, first_name, last_name, email, phone, designation, dept_id)
    VALUES ('EMP1001', 'Fake', 'Faculty', 'fake_unique@univ.ac.in', '9999999999', 'Professor', 1);
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "Duplicate faculty employee_code should have failed!"
    assert "1062" in err or "duplicate entry" in err.lower()
    return True, "Properly rejected with MySQL 1062 duplicate entry error"


def test_unique_duplicate_invoice_no_fails():
    """Attempt to insert fee payment with duplicate invoice_no (INV-2026-001). Must fail with 1062."""
    sql = """
    START TRANSACTION;
    INSERT INTO FEE_PAYMENT (student_id, invoice_no, total_amount, due_date)
    VALUES (1, 'INV-2026-001', 50000.00, '2026-03-01');
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "Duplicate invoice_no should have failed!"
    assert "1062" in err or "duplicate entry" in err.lower()
    return True, "Properly rejected with MySQL 1062 duplicate entry error"


def test_unique_composite_enrollment_pk_fails():
    """Attempt duplicate enrollment for same student and course (1, 1). Must fail with 1062."""
    sql = """
    START TRANSACTION;
    INSERT INTO ENROLLMENT (student_id, course_id, semester_id, enrollment_date)
    VALUES (1, 1, 1, '2026-01-10');
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "Duplicate enrollment composite PK should have failed!"
    assert "1062" in err or "duplicate entry" in err.lower()
    return True, "Properly rejected with MySQL 1062 duplicate entry error"


def test_unique_composite_attendance_pk_fails():
    """Attempt duplicate attendance record for same (student, course, date) (1, 3, '2026-08-01'). Must fail with 1062."""
    sql = """
    START TRANSACTION;
    INSERT INTO ATTENDANCE (student_id, course_id, attendance_date, status)
    VALUES (1, 3, '2026-08-01', 'Present');
    ROLLBACK;
    """
    code, out, err = run_sql_raw(sql)
    assert code != 0, "Duplicate attendance composite PK should have failed!"
    assert "1062" in err or "duplicate entry" in err.lower()
    return True, "Properly rejected with MySQL 1062 duplicate entry error"


def test_connection_baseline():
    """Verify get_db_connection and execute_query work against live database."""
    conn = get_db_connection()
    assert conn is not None
    res = execute_query("SELECT 1 AS alive, @@version AS ver;")
    assert len(res) == 1
    assert "alive" in res[0]
    return True, f"Baseline connection successful (MySQL version: {res[0].get('ver')})"


@pytest.mark.skipif(not os.path.exists("/tmp/mysql.sock"), reason="requires a local MySQL UNIX socket (Linux)")
def test_connection_fallback_socket():
    """Simulate primary socket down: point Config.DB_SOCKET to non-existent socket, fallback to valid socket."""
    original_socket = Config.DB_SOCKET
    original_fallbacks = list(Config.FALLBACK_SOCKETS)
    try:
        Config.DB_SOCKET = "/tmp/simulated_down_primary.sock"
        Config.FALLBACK_SOCKETS = ["/tmp/simulated_down_sec.sock", "/tmp/mysql.sock"]
        
        conn = get_db_connection()
        assert conn is not None
        assert conn.socket == "/tmp/mysql.sock", f"Expected fallback socket /tmp/mysql.sock, got {conn.socket}"
        
        # Test query execution
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT 42 AS num;")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert str(rows[0]["num"]) == "42"
        return True, "Fallback socket correctly resolved and queries execute"
    finally:
        Config.DB_SOCKET = original_socket
        Config.FALLBACK_SOCKETS = original_fallbacks


@pytest.mark.skipif(not os.path.exists("/tmp/mysql.sock"), reason="requires a local MySQL UNIX socket (Linux)")
def test_connection_all_sockets_down_behavior():
    """Empirically test behavior when ALL sockets are missing.
    
    Examine whether MySQLCLIConnection falls back to TCP host/port and how errors are handled.
    """
    original_socket = Config.DB_SOCKET
    original_fallbacks = list(Config.FALLBACK_SOCKETS)
    try:
        Config.DB_SOCKET = "/tmp/dead_1.sock"
        Config.FALLBACK_SOCKETS = ["/tmp/dead_2.sock"]
        
        conn = get_db_connection()
        assert conn.socket is None, "Socket should be None when all sockets down"
        assert conn.host == Config.DB_HOST
        assert conn.port == Config.DB_PORT
        
        # Since TCP loopback is isolated/refused in this environment, attempting execute() should raise RuntimeError
        failed_with_runtime_error = False
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT 1;")
        except RuntimeError as e:
            failed_with_runtime_error = True
            err_msg = str(e)
            assert "Can't connect to MySQL server" in err_msg or "Connection refused" in err_msg or "error executing query" in err_msg
            
        assert failed_with_runtime_error, "Should have raised RuntimeError when TCP connection fails"
        return True, "Properly caught socket exhaustion and reported TCP connection failure"
    finally:
        Config.DB_SOCKET = original_socket
        Config.FALLBACK_SOCKETS = original_fallbacks


def test_connection_port_fallback_missing_in_cli():
    """EMPIRICAL FINDING: MySQLCLIConnection does not support port fallback across FALLBACK_PORTS."""
    original_socket = Config.DB_SOCKET
    original_fallbacks = list(Config.FALLBACK_SOCKETS)
    original_port = Config.DB_PORT
    try:
        Config.DB_SOCKET = "/tmp/dead.sock"
        Config.FALLBACK_SOCKETS = []
        Config.DB_PORT = 3399  # Simulated down primary port
        # In app/config.py, FALLBACK_PORTS is [3307, 3306]
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT 1;")
            return True, "Port fallback worked"
        except RuntimeError as e:
            return False, f"PORT FALLBACK DEFECT: MySQLCLIConnection does not iterate FALLBACK_PORTS when DB_PORT fails: {e}"
    finally:
        Config.DB_SOCKET = original_socket
        Config.FALLBACK_SOCKETS = original_fallbacks
        Config.DB_PORT = original_port


def test_mysql_cli_null_handling_finding():
    """EMPIRICAL FINDING: MySQLCLIConnection returns string 'NULL' instead of Python None for NULL values."""
    res = execute_query("SELECT room_id FROM STUDENT WHERE reg_no = '25BCE0899';")
    assert len(res) == 1
    val = res[0]["room_id"]
    # Document whether it's 'NULL' string or None
    if val == "NULL":
        return False, f"BUG: execute_query returned string 'NULL' ({type(val)}) instead of None for Day Scholar room_id"
    elif val is None:
        return True, "execute_query correctly returned None for NULL value"
    else:
        return False, f"Unexpected value for NULL room_id: {val}"


def test_mysql_cli_information_schema_casing_finding():
    """EMPIRICAL FINDING: information_schema queries return uppercase column names."""
    res = execute_query(
        "SELECT column_name AS column_name FROM information_schema.key_column_usage "
        "WHERE table_schema = 'university_db' AND table_name = 'ENROLLMENT' AND constraint_name = 'PRIMARY';"
    )
    assert len(res) > 0
    first_row = res[0]
    keys = list(first_row.keys())
    if "COLUMN_NAME" in keys and "column_name" not in keys:
        return False, f"KEY MISMATCH: information_schema returned uppercase key {keys!r}, causing test runner KeyError: 'column_name'"
    elif "column_name" in keys:
        return True, "Key is lowercase column_name"
    else:
        return False, f"Unexpected keys: {keys}"


if __name__ == "__main__":
    tests = [
        ("FK Non-existent programme_id", test_fk_nonexistent_programme_fails),
        ("FK Non-existent advisor_id", test_fk_nonexistent_advisor_fails),
        ("FK Non-existent room_id", test_fk_nonexistent_room_fails),
        ("FK Delete Department RESTRICT", test_fk_delete_dept_restrict_fails),
        ("FK Delete Programme RESTRICT", test_fk_delete_programme_restrict_fails),
        ("FK Delete Semester RESTRICT", test_fk_delete_semester_restrict_fails),
        ("FK Delete Room ON DELETE SET NULL", test_fk_delete_room_sets_student_room_null),
        ("FK Delete Student ON DELETE CASCADE", test_fk_delete_student_cascades_to_enrollment_and_fees),
        ("UK Duplicate Student Email", test_unique_duplicate_student_email_fails),
        ("UK Duplicate Student Reg No", test_unique_duplicate_student_reg_no_fails),
        ("UK Duplicate Course Code", test_unique_duplicate_course_code_fails),
        ("UK Duplicate Faculty Email", test_unique_duplicate_faculty_email_fails),
        ("UK Duplicate Faculty Emp Code", test_unique_duplicate_faculty_emp_code_fails),
        ("UK Duplicate Invoice No", test_unique_duplicate_invoice_no_fails),
        ("Composite PK Duplicate Enrollment", test_unique_composite_enrollment_pk_fails),
        ("Composite PK Duplicate Attendance", test_unique_composite_attendance_pk_fails),
        ("Connection Baseline", test_connection_baseline),
        ("Connection Fallback Socket", test_connection_fallback_socket),
        ("Connection All Sockets Down", test_connection_all_sockets_down_behavior),
        ("Connection Port Fallback in CLI", test_connection_port_fallback_missing_in_cli),
        ("Data Type NULL Handling", test_mysql_cli_null_handling_finding),
        ("Information Schema Casing", test_mysql_cli_information_schema_casing_finding),
    ]

    print("=" * 70)
    print("CHALLENGER M1 EMPIRICAL TEST HARNESS EXECUTION")
    print("=" * 70)
    passed = 0
    failed = 0
    for name, test_func in tests:
        try:
            status, msg = test_func()
            if status:
                print(f"[PASS] {name}: {msg}")
                passed += 1
            else:
                print(f"[FINDING / FAIL] {name}: {msg}")
                failed += 1
        except Exception as e:
            print(f"[ERROR] {name}: Unhandled exception: {e}")
            failed += 1

    print("=" * 70)
    print(f"SUMMARY: Total={len(tests)}, Passed={passed}, Failures/Findings={failed}")
    print("=" * 70)
