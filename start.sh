#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=== Student University Management System (UMS) ==="

# 1. Ensure MySQL daemon is running
"$DIR/run_mysql.sh"

# 2. Check virtual environment
if [ ! -f "$DIR/venv/bin/python3" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$DIR/venv"
    "$DIR/venv/bin/pip" install -r "$DIR/requirements.txt"
fi

# 3. Start Flask web server
echo "Starting Flask web application on http://localhost:5000 ..."
exec "$DIR/venv/bin/python3" "$DIR/run.py"
