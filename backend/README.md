# Backend (FastAPI + SQLite)

This folder contains a minimal FastAPI backend scaffold with endpoints used by the frontend:

- `POST /api/contact` — save contact messages
- `POST /api/booking` — create bookings
- `GET /api/students` — list registered students
- `POST /api/signup` — register a user (used for email signups / OAuth user storage)
- Admin routes under `/admin` protected by `x-admin-token` header (set `ADMIN_TOKEN` env var)
- `GET /sitemap.xml` and `GET /robots.txt`

See `db_init.py` to initialize the SQLite database.

Environment variables:
- `ADMIN_TOKEN` — token for admin endpoints
- `SITE_HOST` — public site host used in sitemap/robots
