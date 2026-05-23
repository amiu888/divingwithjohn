import os
import sqlite3
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from models import (
    ContactCreate, BookingCreate, UserCreate, CourseIn,
    TestimonialIn, GalleryItemIn, FAQItemIn, LocationIn
)

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "divingwithjohn.db"

app = FastAPI(title="Diving with John API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def require_admin(x_admin_token: Optional[str]):
    token = os.getenv("ADMIN_TOKEN")
    if not token or x_admin_token != token:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ── PUBLIC ──────────────────────────────────────────────

@app.post('/api/contact')
def create_contact(payload: ContactCreate):
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO contacts (name,email,message) VALUES (?,?,?)',
              (payload.name, payload.email, payload.message))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post('/api/booking')
def create_booking(payload: BookingCreate):
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO bookings (course_id,user_email,date) VALUES (?,?,?)',
              (payload.course_id, payload.user_email, payload.date))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post('/api/signup')
def signup(user: UserCreate):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (email,name,provider,provider_id) VALUES (?,?,?,?)',
                  (user.email, user.name, user.provider, user.provider_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail='Email already registered')
    conn.close()
    return {"status": "ok"}

@app.get('/api/testimonials')
def public_testimonials():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM testimonials WHERE enabled=1 ORDER BY sort_order,id')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get('/api/gallery')
def public_gallery():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM gallery_items WHERE enabled=1 ORDER BY sort_order,id')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get('/api/faq')
def public_faq():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM faq_items WHERE enabled=1 ORDER BY sort_order,id')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get('/api/locations')
def public_locations():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM locations WHERE enabled=1 ORDER BY sort_order,id')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get('/api/sections')
def public_sections():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT key,enabled FROM sections')
    rows = c.fetchall()
    conn.close()
    return {r['key']: bool(r['enabled']) for r in rows}


# ── ADMIN: STUDENTS ──────────────────────────────────────

@app.get('/api/students')
def list_students():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id,email,name,provider,created_at FROM users')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get('/admin/students')
def list_students_admin(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM users ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── ADMIN: COURSES ───────────────────────────────────────

@app.get('/admin/courses')
def list_courses(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM courses ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post('/admin/courses')
def create_course(course: CourseIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO courses (title,description,level,stars,depth) VALUES (?,?,?,?,?)',
              (course.title, course.description, course.level, course.stars, course.depth))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.put('/admin/courses/{course_id}')
def update_course(course_id: int, course: CourseIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE courses SET title=?,description=?,level=?,stars=?,depth=? WHERE id=?',
              (course.title, course.description, course.level, course.stars, course.depth, course_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post('/admin/courses/{course_id}/suspend')
def suspend_course(course_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE courses SET suspended=1 WHERE id=?', (course_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post('/admin/courses/{course_id}/archive')
def archive_course(course_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE courses SET archived=1 WHERE id=?', (course_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post('/admin/courses/{course_id}/restore')
def restore_course(course_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE courses SET suspended=0,archived=0 WHERE id=?', (course_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete('/admin/courses/{course_id}')
def delete_course(course_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM courses WHERE id=?', (course_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


# ── ADMIN: CONTACTS & BOOKINGS ───────────────────────────

@app.get('/admin/contacts')
def list_contacts(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM contacts ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get('/admin/bookings')
def list_bookings(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM bookings ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── ADMIN: TESTIMONIALS ──────────────────────────────────

@app.get('/admin/testimonials')
def list_testimonials(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM testimonials ORDER BY sort_order,id')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post('/admin/testimonials')
def create_testimonial(item: TestimonialIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO testimonials (name,location,quote,stars,sort_order) VALUES (?,?,?,?,?)',
              (item.name, item.location, item.quote, item.stars, item.sort_order))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.put('/admin/testimonials/{item_id}')
def update_testimonial(item_id: int, item: TestimonialIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE testimonials SET name=?,location=?,quote=?,stars=?,sort_order=? WHERE id=?',
              (item.name, item.location, item.quote, item.stars, item.sort_order, item_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post('/admin/testimonials/{item_id}/toggle')
def toggle_testimonial(item_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE testimonials SET enabled = 1 - enabled WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete('/admin/testimonials/{item_id}')
def delete_testimonial(item_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM testimonials WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


# ── ADMIN: GALLERY ───────────────────────────────────────

@app.get('/admin/gallery')
def list_gallery(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM gallery_items ORDER BY sort_order,id')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post('/admin/gallery')
def create_gallery_item(item: GalleryItemIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO gallery_items (icon,caption,sort_order) VALUES (?,?,?)',
              (item.icon, item.caption, item.sort_order))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.put('/admin/gallery/{item_id}')
def update_gallery_item(item_id: int, item: GalleryItemIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE gallery_items SET icon=?,caption=?,sort_order=? WHERE id=?',
              (item.icon, item.caption, item.sort_order, item_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post('/admin/gallery/{item_id}/toggle')
def toggle_gallery_item(item_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE gallery_items SET enabled = 1 - enabled WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete('/admin/gallery/{item_id}')
def delete_gallery_item(item_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM gallery_items WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


# ── ADMIN: FAQ ───────────────────────────────────────────

@app.get('/admin/faq')
def list_faq(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM faq_items ORDER BY sort_order,id')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post('/admin/faq')
def create_faq(item: FAQItemIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO faq_items (question,answer,sort_order) VALUES (?,?,?)',
              (item.question, item.answer, item.sort_order))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.put('/admin/faq/{item_id}')
def update_faq(item_id: int, item: FAQItemIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE faq_items SET question=?,answer=?,sort_order=? WHERE id=?',
              (item.question, item.answer, item.sort_order, item_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post('/admin/faq/{item_id}/toggle')
def toggle_faq(item_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE faq_items SET enabled = 1 - enabled WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete('/admin/faq/{item_id}')
def delete_faq(item_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM faq_items WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


# ── ADMIN: LOCATIONS ─────────────────────────────────────

@app.get('/admin/locations')
def list_locations(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM locations ORDER BY sort_order,id')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post('/admin/locations')
def create_location(item: LocationIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO locations (flag,name,description,sort_order) VALUES (?,?,?,?)',
              (item.flag, item.name, item.description, item.sort_order))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.put('/admin/locations/{item_id}')
def update_location(item_id: int, item: LocationIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE locations SET flag=?,name=?,description=?,sort_order=? WHERE id=?',
              (item.flag, item.name, item.description, item.sort_order, item_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post('/admin/locations/{item_id}/toggle')
def toggle_location(item_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE locations SET enabled = 1 - enabled WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete('/admin/locations/{item_id}')
def delete_location(item_id: int, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM locations WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


# ── ADMIN: SECTIONS ──────────────────────────────────────

@app.get('/admin/sections')
def list_sections(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM sections')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post('/admin/sections/{key}/toggle')
def toggle_section(key: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE sections SET enabled = 1 - enabled WHERE key=?', (key,))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Section not found")
    conn.commit()
    conn.close()
    return {"status": "ok"}


# ── SEO / UTILS ──────────────────────────────────────────

@app.get('/sitemap.xml', response_class=PlainTextResponse)
def sitemap():
    host = os.getenv('SITE_HOST', 'https://example.com')
    pages = ["/", "/courses", "/about", "/blog", "/faq"]
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id FROM courses WHERE archived=0')
    rows = c.fetchall()
    conn.close()
    for r in rows:
        pages.append(f"/courses/{r['id']}")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for p in pages:
        xml += f"  <url><loc>{host}{p}</loc></url>\n"
    xml += "</urlset>"
    return xml

@app.get('/robots.txt', response_class=PlainTextResponse)
def robots():
    host = os.getenv('SITE_HOST', 'https://example.com')
    return f"User-agent: *\nAllow: /\nSitemap: {host}/sitemap.xml\n"

FRONTEND_DIR = PROJECT_ROOT / "frontend"

@app.get("/", response_class=HTMLResponse)
def serve_index():
    return HTMLResponse(content=(FRONTEND_DIR / "index.html").read_text(), status_code=200)

@app.get("/admin.html", response_class=HTMLResponse)
def serve_admin():
    return HTMLResponse(content=(FRONTEND_DIR / "admin.html").read_text(), status_code=200)

@app.get("/test.html", response_class=HTMLResponse)
def serve_test():
    path = FRONTEND_DIR / "test.html"
    if path.exists():
        return HTMLResponse(content=path.read_text(), status_code=200)

# Static assets fallback
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
