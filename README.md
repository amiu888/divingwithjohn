divingwithjohn
=================

Scaffolded project for John — frontend snapshot (from Framer) and Python FastAPI backend using SQLite.

Layout:
- `frontend/` — exported HTML snapshot (index.html)
- `backend/` — FastAPI app, DB init, and API endpoints
- `divingwithjohn.db` — SQLite database (created on first run)

Run backend (development):

```bash
cd /Users/afonso/Workspace/divingwithjohn/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python db_init.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend can be deployed to Cloudflare Pages; backend can be deployed separately (Cloudflare Workers with D1 is possible but this scaffold uses SQLite locally).
