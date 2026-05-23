#!/usr/bin/env bash
set -e

cd /workspace/backend
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Initialise the database if it doesn't exist yet
if [ ! -f /workspace/divingwithjohn.db ]; then
  python db_init.py
fi

echo ""
echo "Setup complete."
echo "  Start backend : cd backend && source .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "  Serve frontend: cd frontend && python -m http.server 3000"
