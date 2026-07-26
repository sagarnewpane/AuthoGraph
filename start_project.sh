#!/usr/bin/env bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

if [[ ! -x "$VENV_DIR/bin/python" || ! -d "$PROJECT_DIR/frontend/node_modules" ]]; then
    echo "Project dependencies are missing. Run ./setup_project.sh first."
    exit 1
fi

cleanup() {
    trap - EXIT INT TERM
    echo
    echo "Stopping servers..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup EXIT
trap 'exit 130' INT TERM

echo "Starting Django at http://127.0.0.1:8000..."
(
    cd "$PROJECT_DIR/backend"
    "$VENV_DIR/bin/python" manage.py runserver
) &
BACKEND_PID=$!

echo "Starting SvelteKit at http://localhost:5173..."
(
    cd "$PROJECT_DIR/frontend"
    npm run dev
) &
FRONTEND_PID=$!

echo "Press Ctrl+C to stop both servers."
wait "$BACKEND_PID" "$FRONTEND_PID"
