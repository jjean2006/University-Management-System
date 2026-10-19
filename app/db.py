"""Database Connection and Query Execution Service.

Provides a unified interface to MySQL with multi-tiered fallback:
  1. mysql.connector (TCP / UNIX domain socket)
  2. PyMySQL (TCP / UNIX domain socket)
  3. Native /usr/bin/mysql CLI subshell execution with persistent session and transaction support
All tiers support dictionary cursors, parameterized queries, and transaction commits.
"""

from decimal import Decimal
import os
import re
import select
import subprocess
import time
import uuid
from app.config import Config

# Attempt driver imports
try:
    import mysql.connector
    from mysql.connector import errorcode
    HAS_MYSQL_CONNECTOR = True
except ImportError:
    HAS_MYSQL_CONNECTOR = False

try:
    import pymysql
    import pymysql.cursors
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False


class CaseInsensitiveDict(dict):
    """Dictionary supporting case-insensitive key access while preserving original keys."""

    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        if isinstance(key, str):
            lower_key = key.lower()
            for k in self:
                if isinstance(k, str) and k.lower() == lower_key:
                    return super().__getitem__(k)
        return super().__getitem__(key)

    def __contains__(self, key):
        if super().__contains__(key):
            return True
        if isinstance(key, str):
            lower_key = key.lower()
            return any(isinstance(k, str) and k.lower() == lower_key for k in self)
        return False

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


class MySQLCLIConnection:
    """DB-API 2.0 style connection wrapper using /usr/bin/mysql CLI with stateful transaction support."""

    def __init__(self, user, password, db, socket=None, host="127.0.0.1", port=3307, fallback_ports=None):
        self.user = user
        self.password = password
        self.db = db
        self.socket = socket
        self.host = host
        self.port = port
        self.fallback_ports = list(fallback_ports) if fallback_ports else []
        self.is_open = True
        self._proc = None
        self.in_transaction = False

    def cursor(self, dictionary=True):
        if not self.is_open:
            raise RuntimeError("Cannot open cursor on closed connection")
        return MySQLCLICursor(self, dictionary=dictionary)

    def _get_proc(self):
        if self._proc is not None:
            if self._proc.poll() is None:
                return self._proc
            self._proc = None

        if not self.is_open:
            raise RuntimeError("Cannot execute query on closed connection")

        env = os.environ.copy()
        if self.password:
            env["MYSQL_PWD"] = self.password

        # 1. Socket connection if available
        if self.socket and os.path.exists(self.socket):
            cmd = ["/usr/bin/mysql", f"-u{self.user}", "-S", self.socket, "--unbuffered", "--batch", "--force"]
            if self.db:
                cmd.append(self.db)
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1
            )
            return self._proc

        # 2. TCP connection with fallback across configured ports
        candidate_ports = [self.port] + [p for p in self.fallback_ports if p != self.port]
        last_err = None
        for p in candidate_ports:
            cmd = ["/usr/bin/mysql", f"-u{self.user}", "-h", self.host, "-P", str(p), "--unbuffered", "--batch", "--force"]
            if self.db:
                cmd.append(self.db)
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    bufsize=1
                )
                probe_marker = f"__PRB_{uuid.uuid4().hex[:8]}__"
                proc.stdin.write(f"SELECT '{probe_marker}' AS __pr;\n")
                proc.stdin.flush()
                time.sleep(0.01)
                if proc.poll() is not None:
                    err = proc.stderr.read().strip()
                    last_err = err or f"Process exited with code {proc.poll()}"
                    continue
                # Wait for probe
                got_probe = False
                start_time = time.time()
                while time.time() - start_time < 1.0:
                    r, _, _ = select.select([proc.stdout], [], [], 0.1)
                    if r:
                        line = proc.stdout.readline()
                        if probe_marker in line:
                            got_probe = True
                            break
                    if proc.poll() is not None:
                        break
                if got_probe:
                    self.port = p
                    self._proc = proc
                    return self._proc
                else:
                    proc.terminate()
                    try:
                        proc.wait(timeout=0.2)
                    except Exception:
                        pass
            except Exception as e:
                last_err = str(e)

        err_msg = last_err or f"Could not connect to MySQL server on host {self.host} with ports {candidate_ports}"
        raise RuntimeError(f"Database error executing query: {err_msg}")

    @staticmethod
    def _read_proc_stderr(proc):
        parts = []
        while True:
            r, _, _ = select.select([proc.stderr], [], [], 0.02)
            if not r:
                break
            try:
                chunk = os.read(proc.stderr.fileno(), 4096).decode("utf-8", errors="replace")
                if not chunk:
                    break
                parts.append(chunk)
            except OSError:
                break
        raw_err = "".join(parts).strip()
        err_lines = [
            line for line in raw_err.split("\n")
            if not line.startswith("mysql: [Warning]")
            and not line.startswith("[Warning]")
            and not line.startswith("[Note]")
            and line.strip() != ""
        ]
        return "\n".join(err_lines).strip()

    def _execute_sql(self, formatted_sql, cursor=None):
        proc = self._get_proc()
        clean_sql = formatted_sql.strip().rstrip(";")
        upper_sql = clean_sql.upper()

        is_select = upper_sql.startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "WITH"))
        is_tx_ctrl = upper_sql.startswith(("START TRANSACTION", "COMMIT", "ROLLBACK", "BEGIN", "SET AUTOCOMMIT", "SET SESSION"))
        is_insert = upper_sql.startswith("INSERT")

        marker = f"__M_{uuid.uuid4().hex[:8]}__"

        if is_select or is_tx_ctrl:
            if upper_sql.startswith(("START TRANSACTION", "BEGIN")):
                self.in_transaction = True
            elif upper_sql.startswith(("COMMIT", "ROLLBACK")):
                self.in_transaction = False
            cmd = f"{clean_sql};\nSELECT '{marker}' AS __marker;\n"
        else:
            cmd = f"{clean_sql};\nSELECT ROW_COUNT() AS __rc, LAST_INSERT_ID() AS __lid;\nSELECT '{marker}' AS __marker;\n"

        try:
            proc.stdin.write(cmd)
            proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            self._proc = None
            raise RuntimeError(f"Database error executing query: MySQL connection broken ({e})")

        lines = []
        start_time = time.time()
        timeout = 30.0
        while True:
            if time.time() - start_time > timeout:
                self.close()
                raise TimeoutError("Database query timed out waiting for MySQL response")
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    err = proc.stderr.read().strip()
                    self._proc = None
                    raise RuntimeError(f"Database error executing query: {err}")
                break
            l = line.strip()
            if l == marker:
                break
            lines.append(l)

        if lines and lines[-1] == "__marker":
            lines.pop()

        err = self._read_proc_stderr(proc)
        if err and "ERROR" in err:
            raise RuntimeError(f"Database error executing query: {err}")

        if cursor is not None:
            cursor.description = []
            cursor.rows = []
            cursor.idx = 0
            if is_select:
                if not lines:
                    cursor.rowcount = 0
                    return
                headers = lines[0].split("\t")
                cursor.description = [(h,) for h in headers]
                cleaned_rows = []
                for row_line in lines[1:]:
                    vals = [None if v == "NULL" else v for v in row_line.split("\t")]
                    while len(vals) < len(headers):
                        vals.append(None)
                    cleaned_rows.append(vals)

                if cursor.dictionary:
                    dict_rows = []
                    for row in cleaned_rows:
                        d = CaseInsensitiveDict()
                        for h, v in zip(headers, row):
                            d[h] = v
                            if isinstance(h, str):
                                d[h.lower()] = v
                        dict_rows.append(d)
                    cursor.rows = dict_rows
                else:
                    cursor.rows = [tuple(r) for r in cleaned_rows]
                cursor.rowcount = len(cursor.rows)
            elif is_tx_ctrl:
                cursor.rowcount = 0
                cursor.lastrowid = 0
            else:
                rc = 0
                lid = 0
                if len(lines) >= 2:
                    val_parts = lines[1].split("\t")
                    try:
                        rc = int(val_parts[0])
                        lid = int(val_parts[1])
                    except (ValueError, IndexError):
                        pass
                if rc == -1 and err:
                    raise RuntimeError(f"Database error executing query: {err}")
                cursor.rowcount = max(0, rc)
                cursor.lastrowid = lid if is_insert else 0

    def commit(self):
        if self._proc is not None and self._proc.poll() is None:
            self._execute_sql("COMMIT;")
        self.in_transaction = False

    def rollback(self):
        if self._proc is not None and self._proc.poll() is None:
            self._execute_sql("ROLLBACK;")
        self.in_transaction = False

    def close(self):
        self.is_open = False
        if self._proc is not None:
            try:
                if self._proc.poll() is None:
                    try:
                        self._proc.stdin.write("QUIT;\n")
                        self._proc.stdin.flush()
                    except Exception:
                        pass
                    self._proc.terminate()
                    self._proc.wait(timeout=1.0)
            except Exception:
                pass
            finally:
                self._proc = None

    def is_connected(self):
        return self.is_open

    def ping(self, reconnect=True):
        if not self.is_open:
            if reconnect:
                self.is_open = True
                self._proc = None
            else:
                raise RuntimeError("Connection closed")
        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()


class MySQLCLICursor:
    """Cursor wrapper for executing queries via /usr/bin/mysql CLI."""

    def __init__(self, connection, dictionary=True):
        self.connection = connection
        self.dictionary = dictionary
        self.rows = []
        self.description = []
        self.rowcount = 0
        self.lastrowid = 0
        self.idx = 0

    @staticmethod
    def _escape_param(p):
        if p is None:
            return "NULL"
        elif isinstance(p, bool):
            return "1" if p else "0"
        elif isinstance(p, (int, float, Decimal)):
            return str(p)
        else:
            s = str(p).replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
            return f"'{s}'"

    def _format_sql(self, sql, params):
        if params is None:
            return sql
        if isinstance(params, (list, tuple)):
            if len(params) == 0 and "%s" not in sql:
                return sql
            escaped = [self._escape_param(p) for p in params]
            parts = sql.split("%s")
            if len(parts) - 1 != len(escaped):
                raise ValueError(f"Query expects {len(parts) - 1} parameters, got {len(escaped)}")
            return "".join(part + val for part, val in zip(parts, escaped + [""]))
        elif isinstance(params, dict):
            def replacer(match):
                key = match.group(1)
                if key not in params:
                    raise KeyError(f"Parameter '{key}' not provided in params dict")
                return self._escape_param(params[key])
            return re.sub(r"%\(([a-zA-Z0-9_]+)\)s", replacer, sql)
        return sql

    def execute(self, sql, params=None):
        formatted_sql = self._format_sql(sql, params)
        self.connection._execute_sql(formatted_sql, cursor=self)

    def fetchall(self):
        return self.rows

    def fetchone(self):
        if self.idx < len(self.rows):
            row = self.rows[self.idx]
            self.idx += 1
            return row
        return None

    def fetchmany(self, size=None):
        if size is None:
            size = 1
        end = min(self.idx + size, len(self.rows))
        res = self.rows[self.idx:end]
        self.idx = end
        return res

    def close(self):
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def _try_mysql_connector(db_name=None):
    if not HAS_MYSQL_CONNECTOR:
        return None
    db = db_name if db_name is not None else Config.DB_NAME
    # 1. Try sockets
    for sock in [Config.DB_SOCKET] + Config.FALLBACK_SOCKETS:
        if sock and os.path.exists(sock):
            try:
                conn = mysql.connector.connect(
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=db,
                    unix_socket=sock,
                    autocommit=True
                )
                if conn.is_connected():
                    return conn
            except Exception:
                pass
    # 2. Try TCP ports
    for port in [Config.DB_PORT] + Config.FALLBACK_PORTS:
        try:
            conn = mysql.connector.connect(
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=db,
                host=Config.DB_HOST,
                port=port,
                autocommit=True,
                connection_timeout=2
            )
            if conn.is_connected():
                return conn
        except Exception:
            pass
    return None


def _try_pymysql(db_name=None):
    if not HAS_PYMYSQL:
        return None
    db = db_name if db_name is not None else Config.DB_NAME
    # 1. Try sockets
    for sock in [Config.DB_SOCKET] + Config.FALLBACK_SOCKETS:
        if sock and os.path.exists(sock):
            try:
                conn = pymysql.connect(
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=db,
                    unix_socket=sock,
                    autocommit=True,
                    cursorclass=pymysql.cursors.DictCursor
                )
                return conn
            except Exception:
                pass
    # 2. Try TCP ports
    for port in [Config.DB_PORT] + Config.FALLBACK_PORTS:
        try:
            conn = pymysql.connect(
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=db,
                host=Config.DB_HOST,
                port=port,
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=2
            )
            return conn
        except Exception:
            pass
    return None


def _get_cli_connection(db_name=None):
    db = db_name if db_name is not None else Config.DB_NAME
    # Find existing socket
    socket = None
    for s in [Config.DB_SOCKET] + Config.FALLBACK_SOCKETS:
        if s and os.path.exists(s):
            socket = s
            break

    fallback_ports = [p for p in Config.FALLBACK_PORTS if p != Config.DB_PORT]

    # If socket is not reachable, probe configured ports to select an active one
    active_port = Config.DB_PORT
    if not socket:
        for p in [Config.DB_PORT] + fallback_ports:
            env = os.environ.copy()
            if Config.DB_PASSWORD:
                env["MYSQL_PWD"] = Config.DB_PASSWORD
            probe_cmd = ["/usr/bin/mysql", f"-u{Config.DB_USER}", "-h", Config.DB_HOST, "-P", str(p), "-e", "SELECT 1;"]
            if db:
                probe_cmd.append(db)
            try:
                res = subprocess.run(probe_cmd, env=env, capture_output=True, text=True, timeout=1.0)
                if res.returncode == 0:
                    active_port = p
                    break
            except Exception:
                pass

    return MySQLCLIConnection(
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        db=db,
        socket=socket,
        host=Config.DB_HOST,
        port=active_port,
        fallback_ports=fallback_ports
    )


def get_db_connection(db_name=None):
    """Returns an active MySQL connection supporting dictionary cursors.
    
    Tries mysql.connector, then PyMySQL, and falls back to MySQLCLIConnection.
    """
    conn = _try_mysql_connector(db_name)
    if conn:
        return conn

    conn = _try_pymysql(db_name)
    if conn:
        return conn

    return _get_cli_connection(db_name)


def execute_query(sql, params=None, fetch_all=True, fetch_one=False, commit=False):
    """Executes a single SQL query and returns dictionary rows for SELECT or rowcount/lastrowid.
    
    Args:
        sql: SQL query string.
        params: Optional tuple, list, or dict of query parameters.
        fetch_all: If True, returns all matched rows as list of dicts.
        fetch_one: If True, returns a single dict row or None.
        commit: If True, commits transaction.
    """
    conn = get_db_connection()
    try:
        upper_sql = sql.strip().lstrip("(\t\r\n ").upper()
        is_select = upper_sql.startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "WITH"))

        if isinstance(conn, MySQLCLIConnection):
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params)
            if is_select:
                if fetch_one:
                    return cursor.fetchone()
                return cursor.fetchall()
            else:
                if commit:
                    conn.commit()
                lastrowid = getattr(cursor, "lastrowid", 0)
                rowcount = getattr(cursor, "rowcount", 0)
                return lastrowid or rowcount
        else:
            # Native mysql-connector or pymysql
            if hasattr(conn, "cursor"):
                if HAS_MYSQL_CONNECTOR and isinstance(conn, mysql.connector.connection_cext.CMySQLConnection if hasattr(mysql.connector, "connection_cext") else object):
                    cursor = conn.cursor(dictionary=True)
                elif HAS_PYMYSQL and isinstance(conn, pymysql.connections.Connection):
                    cursor = conn.cursor(pymysql.cursors.DictCursor)
                else:
                    try:
                        cursor = conn.cursor(dictionary=True)
                    except TypeError:
                        cursor = conn.cursor()

            cursor.execute(sql, params or ())

            if is_select:
                if fetch_one:
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
                cursor.close()
                return result
            else:
                if commit and hasattr(conn, "commit"):
                    conn.commit()
                rowcount = cursor.rowcount
                lastrowid = getattr(cursor, "lastrowid", 0)
                cursor.close()
                return lastrowid or rowcount
    finally:
        if hasattr(conn, "close"):
            conn.close()


def execute_script(sql_script, db_name=None):
    """Executes a multi-statement SQL script (DDL / seeds)."""
    target_db = db_name if db_name is not None else Config.DB_NAME
    socket = None
    for s in [Config.DB_SOCKET] + Config.FALLBACK_SOCKETS:
        if s and os.path.exists(s):
            socket = s
            break

    env = os.environ.copy()
    if Config.DB_PASSWORD:
        env["MYSQL_PWD"] = Config.DB_PASSWORD

    cmd = ["/usr/bin/mysql", f"-u{Config.DB_USER}"]
    if socket:
        cmd.extend(["-S", socket])
    else:
        cmd.extend(["-h", Config.DB_HOST, "-P", str(Config.DB_PORT)])
    if target_db:
        cmd.append(target_db)

    proc = subprocess.run(cmd, input=sql_script, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        err = proc.stderr.strip() or f"Script execution failed with code {proc.returncode}"
        raise RuntimeError(f"Error executing SQL script: {err}")
    return True
