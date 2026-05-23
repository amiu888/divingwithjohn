# Deploying Frontend to Cloudflare Pages

1. Create a Cloudflare Pages project and connect to your repo.
2. Set the build settings to use a simple `None` build (static folder) or point to `frontend/`.
3. Upload the static files from `frontend/` (index.html and assets).
4. Configure the site domain and enable HTTPS.

Backend: this scaffold uses SQLite and is intended to run separately (e.g., on a small VM, Render, Railway, or Cloudflare Pages Functions rewritten for Workers + D1).
