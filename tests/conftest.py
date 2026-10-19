"""Test configuration and shared fixtures for University Management System (UMS).

Supports multi-port MySQL connectivity (3307 / 3306 / socket),
Flask test client instantiation with session isolation, and
pre-authenticated fixtures for all 5 demo user roles.
"""

import os
import sys
import subprocess
import shutil
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_CONFIG = {
    "user": "jacob",
    "password": "password",
    "database": "university_db",
    "host": "127.0.0.1",
    "ports": [3307, 3306],
    "socket": "/tmp/mysql.sock",
}

DEMO_CREDENTIALS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "user_id": 1,
        "entity_id": None,
        "display_name": "System Administrator",
    },
    "faculty": {
        "username": "faculty",
        "alt_username": "EMP1001",
        "password": "faculty123",
        "alt_password": "password",
        "role": "faculty",
        "user_id": 2,
        "entity_id": 1,
        "display_name": "Dr. Ramesh Kumar",
    },
    "student": {
        "username": "student",
        "alt_username": "25BAI0077",
        "password": "student123",
        "alt_password": "password",
        "role": "student",
        "user_id": 3,
        "entity_id": 1,
        "display_name": "Jacob Jean",
    },
    "accounts": {
        "username": "accounts",
        "password": "accounts123",
        "role": "accounts",
        "user_id": 4,
        "entity_id": None,
        "display_name": "University Bursar",
    },
    "warden": {
        "username": "warden",
        "password": "warden123",
        "role": "warden",
        "user_id": 5,
        "entity_id": None,
        "display_name": "Chief Hostel Warden",
    },
}


def _detect_active_db_connection():
    """Detect available MySQL port or socket, returning connection parameters or None."""
    # 1. Check if app.db exists and works
    try:
        from app.db import get_db_connection
        conn = get_db_connection()
        if conn:
            return {"type": "app_db", "conn": conn}
    except Exception:
        pass

    # 2. Try mysql.connector if available
    try:
        import mysql.connector
        for port in DB_CONFIG["ports"]:
            try:
                conn = mysql.connector.connect(
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                    host=DB_CONFIG["host"],
                    port=port,
                    database=DB_CONFIG["database"],
                    connection_timeout=2,
                )
                if conn.is_connected():
                    return {"type": "mysql_connector", "port": port}
            except Exception:
                continue
        if os.path.exists(DB_CONFIG["socket"]):
            try:
                conn = mysql.connector.connect(
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                    unix_socket=DB_CONFIG["socket"],
                    database=DB_CONFIG["database"],
                    connection_timeout=2,
                )
                if conn.is_connected():
                    return {"type": "mysql_connector_socket"}
            except Exception:
                pass
    except ImportError:
        pass

    # 3. Try pymysql if available
    try:
        import pymysql
        for port in DB_CONFIG["ports"]:
            try:
                conn = pymysql.connect(
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                    host=DB_CONFIG["host"],
                    port=port,
                    database=DB_CONFIG["database"],
                    connect_timeout=2,
                )
                return {"type": "pymysql", "port": port}
            except Exception:
                continue
    except ImportError:
        pass

    # 4. Check /usr/bin/mysql CLI
    mysql_bin = shutil.which("mysql")
    if mysql_bin:
        for port in DB_CONFIG["ports"]:
            cmd = [
                mysql_bin,
                f"-u{DB_CONFIG['user']}",
                f"-p{DB_CONFIG['password']}",
                f"-h{DB_CONFIG['host']}",
                f"-P{port}",
                "-e", "SELECT 1;",
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, timeout=2)
                if res.returncode == 0:
                    return {"type": "cli", "port": port}
            except Exception:
                continue

        if os.path.exists(DB_CONFIG["socket"]):
            cmd = [
                mysql_bin,
                f"-u{DB_CONFIG['user']}",
                f"-p{DB_CONFIG['password']}",
                f"-S{DB_CONFIG['socket']}",
                "-e", "SELECT 1;",
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, timeout=2)
                if res.returncode == 0:
                    return {"type": "cli_socket"}
            except Exception:
                pass

    return None


@pytest.fixture(scope="session")
def db_connection_info():
    """Returns detected DB connection info or None."""
    return _detect_active_db_connection()


@pytest.fixture
def db_query(db_connection_info):
    """Fixture providing a unified query runner returning list of dicts.
    
    If database is not running or accessible, skips test gracefully.
    """
    if db_connection_info is None:
        pytest.skip("MySQL database not running or inaccessible on ports 3307/3306 or socket.")

    def _execute(sql, params=None):
        # Strategy A: Use app.db if importable
        try:
            from app.db import execute_query
            return execute_query(sql, params)
        except Exception:
            pass

        # Strategy B: mysql.connector
        try:
            import mysql.connector
            port = db_connection_info.get("port", 3307)
            kwargs = {
                "user": DB_CONFIG["user"],
                "password": DB_CONFIG["password"],
                "database": DB_CONFIG["database"],
            }
            if db_connection_info.get("type") in ("mysql_connector_socket", "cli_socket"):
                kwargs["unix_socket"] = DB_CONFIG["socket"]
            else:
                kwargs["host"] = DB_CONFIG["host"]
                kwargs["port"] = port

            conn = mysql.connector.connect(**kwargs)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params or ())
            if sql.strip().upper().startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")):
                rows = cursor.fetchall()
            else:
                conn.commit()
                rows = cursor.rowcount
            cursor.close()
            conn.close()
            return rows
        except ImportError:
            pass

        # Strategy C: pymysql
        try:
            import pymysql
            from pymysql.cursors import DictCursor
            port = db_connection_info.get("port", 3307)
            kwargs = {
                "user": DB_CONFIG["user"],
                "password": DB_CONFIG["password"],
                "database": DB_CONFIG["database"],
                "cursorclass": DictCursor,
            }
            if db_connection_info.get("type") in ("mysql_connector_socket", "cli_socket"):
                kwargs["unix_socket"] = DB_CONFIG["socket"]
            else:
                kwargs["host"] = DB_CONFIG["host"]
                kwargs["port"] = port

            conn = pymysql.connect(**kwargs)
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                if sql.strip().upper().startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")):
                    rows = cursor.fetchall()
                else:
                    conn.commit()
                    rows = cursor.rowcount
            conn.close()
            return rows
        except ImportError:
            pass

        # Strategy D: CLI fallback
        mysql_bin = shutil.which("mysql")
        if mysql_bin:
            port = db_connection_info.get("port", 3307)
            cmd = [
                mysql_bin,
                f"-u{DB_CONFIG['user']}",
                f"-p{DB_CONFIG['password']}",
                "-D", DB_CONFIG["database"],
                "--batch",
                "--raw",
            ]
            if "socket" in db_connection_info.get("type", ""):
                cmd.append(f"-S{DB_CONFIG['socket']}")
            else:
                cmd.extend([f"-h{DB_CONFIG['host']}", f"-P{port}"])

            # Substitute params into SQL safely if simple
            final_sql = sql
            if params:
                for p in params:
                    if isinstance(p, str):
                        escaped = p.replace("'", "\\'")
                        final_sql = final_sql.replace("%s", f"'{escaped}'", 1)
                    elif p is None:
                        final_sql = final_sql.replace("%s", "NULL", 1)
                    else:
                        final_sql = final_sql.replace("%s", str(p), 1)

            cmd.extend(["-e", final_sql])
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"MySQL CLI failed: {res.stderr}")

            lines = [l for l in res.stdout.strip().split("\n") if l]
            if not lines:
                return []
            headers = lines[0].split("\t")
            rows = []
            for line in lines[1:]:
                vals = line.split("\t")
                row_dict = {}
                for idx, h in enumerate(headers):
                    val = vals[idx] if idx < len(vals) else None
                    if val == "NULL":
                        val = None
                    row_dict[h] = val
                rows.append(row_dict)
            return rows

        raise RuntimeError("No working MySQL execution mechanism found.")

    return _execute


@pytest.fixture(scope="session")
def flask_app():
    """Lazily load the Flask application for integration and client testing."""
    # Try importing create_app from app
    try:
        from app import create_app
        test_app = create_app()
        test_app.config.update({
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key-for-ums",
        })
        return test_app
    except (ImportError, AttributeError):
        pass

    # Try importing app from run or app
    try:
        import app
        if hasattr(app, "app"):
            test_app = getattr(app, "app")
            test_app.config.update({
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SECRET_KEY": "test-secret-key-for-ums",
            })
            return test_app
    except ImportError:
        pass

    try:
        import run
        if hasattr(run, "app"):
            test_app = getattr(run, "app")
            test_app.config.update({
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SECRET_KEY": "test-secret-key-for-ums",
            })
            return test_app
    except ImportError:
        pass

    return None


@pytest.fixture
def client(flask_app):
    """Provides Flask test client, skipping if Flask app is not yet initialized."""
    if flask_app is None:
        pytest.skip("Flask application factory create_app() not yet available.")
    with flask_app.test_client() as c:
        yield c


def _login_client_as_role(client, role):
    """Log in the Flask test client as a specific role."""
    creds = DEMO_CREDENTIALS.get(role.lower())
    if not creds:
        raise ValueError(f"Unknown role: {role}")

    # Set session directly for reliable test isolation
    with client.session_transaction() as sess:
        sess["user_id"] = creds["user_id"]
        sess["username"] = creds["username"]
        sess["role"] = creds["role"]
        sess["entity_id"] = creds["entity_id"]
        sess["display_name"] = creds["display_name"]
        sess["logged_in"] = True

    # Also perform POST /login in case backend requires login route handling
    try:
        client.post(
            "/login",
            data={"username": creds["username"], "password": creds["password"]},
            follow_redirects=True,
        )
    except Exception:
        pass

    return client


@pytest.fixture
def admin_client(client):
    """Flask test client pre-authenticated as Admin."""
    return _login_client_as_role(client, "admin")


@pytest.fixture
def faculty_client(client):
    """Flask test client pre-authenticated as Faculty (EMP1001 / Dr. Ramesh Kumar)."""
    return _login_client_as_role(client, "faculty")


@pytest.fixture
def student_client(client):
    """Flask test client pre-authenticated as Student (25BAI0077 / Jacob Jean)."""
    return _login_client_as_role(client, "student")


@pytest.fixture
def accounts_client(client):
    """Flask test client pre-authenticated as Accounts Officer."""
    return _login_client_as_role(client, "accounts")


@pytest.fixture
def warden_client(client):
    """Flask test client pre-authenticated as Hostel Warden."""
    return _login_client_as_role(client, "warden")
