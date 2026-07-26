#!/usr/bin/env bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "Creating the Python virtual environment..."
"$PYTHON_BIN" -m venv "$VENV_DIR"

echo "Installing backend dependencies..."
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$PROJECT_DIR/backend/requirements.txt"

echo "Creating and migrating the SQLite database..."
(
    cd "$PROJECT_DIR/backend"
    "$VENV_DIR/bin/python" manage.py migrate
)

echo "Installing frontend dependencies..."
(
    cd "$PROJECT_DIR/frontend"
    npm ci
)

echo
echo "Setup complete. Run ./start_project.sh to start Authograph."
