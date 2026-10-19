#!/usr/bin/env python3
"""Database Initialization and Seed Script.

Connects to MySQL as user 'jacob' with password 'password',
creates database 'university_db' if it does not exist,
and sequentially executes:
  1. schema/schema.sql  (12 Relational Tables in topological order)
  2. schema/views.sql   (6 Analytical Views + 2 Supplemental Views)
  3. schema/seed_data.sql (Section 4 DML sample dataset)
Then verifies that all 12 tables exist and seed record counts match Section 4 verbatim.
"""

import os
import sys
import subprocess

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.config import Config
from app.db import execute_script, execute_query


SCHEMA_SQL_PATH = os.path.join(PROJECT_ROOT, "schema", "schema.sql")
VIEWS_SQL_PATH = os.path.join(PROJECT_ROOT, "schema", "views.sql")
SEED_DATA_SQL_PATH = os.path.join(PROJECT_ROOT, "schema", "seed_data.sql")


EXPECTED_TABLES = [
    "DEPARTMENT",
    "SEMESTER",
    "HOSTEL_BLOCK",
    "PROGRAMME",
    "FACULTY",
    "COURSE",
    "HOSTEL_ROOM",
    "STUDENT",
    "ENROLLMENT",
    "ATTENDANCE",
    "COURSE_WAITLIST",
    "FEE_PAYMENT"
]

EXPECTED_COUNTS = {
    "DEPARTMENT": 3,
    "PROGRAMME": 3,
    "FACULTY": 3,
    "SEMESTER": 2,
    "COURSE": 4,
    "HOSTEL_BLOCK": 2,
    "HOSTEL_ROOM": 3,
    "STUDENT": 5,
    "ENROLLMENT": 7,
    "ATTENDANCE": 9,
    "COURSE_WAITLIST": 2,
    "FEE_PAYMENT": 4
}

EXPECTED_VIEWS = [
    "v_admin_student_directory",
    "v_faculty_attendance_shortage",
    "v_accounts_fee_summary",
    "v_accounts_defaulters_list",
    "v_warden_occupancy_overview",
    "v_warden_resident_directory",
    "v_admin_course_waitlist",
    "v_faculty_view"
]


def ensure_database():
    print(f"[*] Ensuring database '{Config.DB_NAME}' exists...")
    create_db_sql = f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME};"
    execute_script(create_db_sql, db_name=None)
    print(f"[+] Database '{Config.DB_NAME}' is ready.")


def apply_schema():
    print(f"[*] Executing schema DDL from {SCHEMA_SQL_PATH}...")
    with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    execute_script(schema_sql, db_name=Config.DB_NAME)
    print("[+] Schema DDL applied successfully (12 tables).")


def apply_views():
    print(f"[*] Executing views DDL from {VIEWS_SQL_PATH}...")
    with open(VIEWS_SQL_PATH, "r", encoding="utf-8") as f:
        views_sql = f.read()
    execute_script(views_sql, db_name=Config.DB_NAME)
    print("[+] Views DDL applied successfully (8 views).")


def apply_seed_data():
    print(f"[*] Populating seed data from {SEED_DATA_SQL_PATH}...")
    with open(SEED_DATA_SQL_PATH, "r", encoding="utf-8") as f:
        seed_sql = f.read()
    execute_script(seed_sql, db_name=Config.DB_NAME)
    print("[+] Seed data inserted successfully.")


def verify_database():
    print("\n" + "=" * 60)
    print("VERIFICATION OF TABLES & ROW COUNTS")
    print("=" * 60)

    # 1. Verify tables
    tables_result = execute_query("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE';")
    existing_tables = set()
    for row in tables_result:
        # Key could be Tables_in_university_db
        table_name = list(row.values())[0]
        existing_tables.add(table_name.upper())

    missing_tables = [t for t in EXPECTED_TABLES if t not in existing_tables]
    if missing_tables:
        print(f"[!] FAILED: Missing tables: {missing_tables}")
        sys.exit(1)
    print(f"[+] All {len(EXPECTED_TABLES)} tables exist in '{Config.DB_NAME}'.")

    # 2. Verify row counts
    count_mismatches = []
    for table, expected_count in EXPECTED_COUNTS.items():
        res = execute_query(f"SELECT COUNT(*) AS cnt FROM {table};", fetch_one=True)
        actual_count = int(res["cnt"])
        status = "OK" if actual_count == expected_count else "MISMATCH"
        print(f"  - {table:<16}: Expected={expected_count}, Actual={actual_count} [{status}]")
        if actual_count != expected_count:
            count_mismatches.append((table, expected_count, actual_count))

    if count_mismatches:
        print(f"[!] FAILED: Row count mismatches detected: {count_mismatches}")
        sys.exit(1)
    print("[+] All table row counts match Section 4 specification exactly.")

    # 3. Verify views
    print("\n" + "=" * 60)
    print("VERIFICATION OF ANALYTICAL & OPERATIONAL VIEWS")
    print("=" * 60)
    views_result = execute_query("SHOW FULL TABLES WHERE Table_type = 'VIEW';")
    existing_views = set()
    for row in views_result:
        view_name = list(row.values())[0]
        existing_views.add(view_name.lower())

    missing_views = [v for v in EXPECTED_VIEWS if v.lower() not in existing_views]
    if missing_views:
        print(f"[!] FAILED: Missing views: {missing_views}")
        sys.exit(1)

    for v in EXPECTED_VIEWS:
        rows = execute_query(f"SELECT * FROM {v};")
        print(f"  - {v:<32}: Returned {len(rows)} rows.")

    print("\n[+] SUCCESS: Database initialization and verification complete!")


def main():
    try:
        ensure_database()
        apply_schema()
        apply_views()
        apply_seed_data()
        verify_database()
    except Exception as e:
        print(f"\n[!] ERROR during database initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
