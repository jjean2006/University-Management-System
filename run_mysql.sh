#!/bin/bash
set -e

SOCKET="/tmp/mysql.sock"
PORT=3307
DATADIR="/tmp/local_mysql"
LOGFILE="${DATADIR}/error.log"

is_mysql_ready() {
    if mysqladmin -u jacob -ppassword -S "$SOCKET" ping >/dev/null 2>&1; then
        return 0
    fi
    if mysqladmin -u root -S "$SOCKET" ping >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

if is_mysql_ready; then
    echo "[run_mysql.sh] MySQL daemon is already running and responding at $SOCKET (port $PORT)."
    exit 0
fi

echo "[run_mysql.sh] Starting MySQL daemon..."

if [ ! -d "$DATADIR" ] || [ ! -f "$DATADIR/ibdata1" ]; then
    echo "[run_mysql.sh] Initializing MySQL datadir at $DATADIR..."
    mkdir -p "$DATADIR"
    /usr/sbin/mysqld --no-defaults --initialize-insecure --datadir="$DATADIR" >/dev/null 2>&1
fi

nohup /usr/sbin/mysqld --no-defaults \
    --innodb-use-native-aio=0 \
    --skip-name-resolve \
    --datadir="$DATADIR" \
    --socket="$SOCKET" \
    --port="$PORT" \
    --bind-address=0.0.0.0 \
    --mysqlx=OFF \
    --log-error="$LOGFILE" >/dev/null 2>&1 &

DAEMON_PID=$!
echo "[run_mysql.sh] Launched mysqld (PID $DAEMON_PID). Waiting for socket to become available..."

STARTED=0
for i in {1..30}; do
    if is_mysql_ready; then
        STARTED=1
        break
    fi
    sleep 0.5
done

if [ $STARTED -eq 0 ]; then
    echo "[run_mysql.sh] ERROR: MySQL server failed to start within 15 seconds."
    if [ -f "$LOGFILE" ]; then
        tail -n 20 "$LOGFILE"
    fi
    exit 1
fi

echo "[run_mysql.sh] MySQL is alive. Ensuring user 'jacob' and 'university_db' exist..."
mysql -u root -S "$SOCKET" -e "
CREATE USER IF NOT EXISTS 'jacob'@'%' IDENTIFIED BY 'password';
ALTER USER 'jacob'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON *.* TO 'jacob'@'%' WITH GRANT OPTION;
CREATE USER IF NOT EXISTS 'jacob'@'localhost' IDENTIFIED BY 'password';
ALTER USER 'jacob'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON *.* TO 'jacob'@'localhost' WITH GRANT OPTION;
CREATE DATABASE IF NOT EXISTS university_db;
FLUSH PRIVILEGES;
" >/dev/null 2>&1 || true

echo "[run_mysql.sh] MySQL daemon is running successfully on socket $SOCKET and port $PORT."
exit 0
