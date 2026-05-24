import os
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Attr
import boto3
from mangum import Mangum
from models import (
    ContactCreate, BookingCreate, UserCreate, CourseIn,
    TestimonialIn, GalleryItemIn, FAQItemIn, LocationIn
)

load_dotenv()

app = FastAPI(title="Diving with John API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


def get_dynamodb():
    kwargs = {'region_name': os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')
    if endpoint_url:
        kwargs['endpoint_url'] = endpoint_url
        kwargs['aws_access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID', 'local')
        kwargs['aws_secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY', 'local')
    return boto3.resource('dynamodb', **kwargs)

_admin_token_cache: Optional[str] = None

def get_admin_token() -> Optional[str]:
    global _admin_token_cache
    if _admin_token_cache:
        return _admin_token_cache
    # Local dev: use env var
    local = os.getenv('ADMIN_TOKEN')
    if local:
        _admin_token_cache = local
        return _admin_token_cache
    # Production: read from SSM Parameter Store
    ssm = boto3.client('ssm', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
    resp = ssm.get_parameter(Name='/divingwithjohn/admin-token', WithDecryption=True)
    _admin_token_cache = resp['Parameter']['Value']
    return _admin_token_cache

def tbl(name: str):
    return get_dynamodb().Table(f'dwj_{name}')

def clean(item: dict) -> dict:
    return {k: (int(v) if isinstance(v, Decimal) and v % 1 == 0 else float(v) if isinstance(v, Decimal) else v)
            for k, v in item.items()}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def require_admin(x_admin_token: Optional[str]):
    token = get_admin_token()
    if not token or x_admin_token != token:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ── PUBLIC ──────────────────────────────────────────────

@app.post('/api/contact')
def create_contact(payload: ContactCreate):
    tbl('contacts').put_item(Item={
        'id': str(uuid4()),
        'name': payload.name or '',
        'email': str(payload.email),
        'message': payload.message,
        'created_at': now_iso(),
    })
    return {"status": "ok"}

@app.post('/api/booking')
def create_booking(payload: BookingCreate):
    tbl('bookings').put_item(Item={
        'id': str(uuid4()),
        'course_id': str(payload.course_id),
        'user_email': str(payload.user_email),
        'date': payload.date,
        'status': 'pending',
        'created_at': now_iso(),
    })
    return {"status": "ok"}

@app.post('/api/signup')
def signup(user: UserCreate):
    users_table = tbl('users')
    if users_table.get_item(Key={'email': str(user.email)}).get('Item'):
        raise HTTPException(status_code=400, detail='Email already registered')
    users_table.put_item(Item={
        'email': str(user.email),
        'name': user.name or '',
        'provider': user.provider or '',
        'provider_id': user.provider_id or '',
        'created_at': now_iso(),
    })
    return {"status": "ok"}

@app.get('/api/testimonials')
def public_testimonials():
    items = [clean(i) for i in tbl('testimonials').scan(FilterExpression=Attr('enabled').eq(1))['Items']]
    return sorted(items, key=lambda x: (int(x.get('sort_order', 0)), x.get('id', '')))

@app.get('/api/gallery')
def public_gallery():
    items = [clean(i) for i in tbl('gallery').scan(FilterExpression=Attr('enabled').eq(1))['Items']]
    return sorted(items, key=lambda x: (int(x.get('sort_order', 0)), x.get('id', '')))

@app.get('/api/faq')
def public_faq():
    items = [clean(i) for i in tbl('faq').scan(FilterExpression=Attr('enabled').eq(1))['Items']]
    return sorted(items, key=lambda x: (int(x.get('sort_order', 0)), x.get('id', '')))

@app.get('/api/locations')
def public_locations():
    items = [clean(i) for i in tbl('locations').scan(FilterExpression=Attr('enabled').eq(1))['Items']]
    return sorted(items, key=lambda x: (int(x.get('sort_order', 0)), x.get('id', '')))

@app.get('/api/sections')
def public_sections():
    items = tbl('sections').scan()['Items']
    return {i['key']: bool(int(i.get('enabled', 1))) for i in items}


# ── ADMIN: STUDENTS ──────────────────────────────────────

@app.get('/admin/students')
def list_students(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    items = [clean(i) for i in tbl('users').scan()['Items']]
    return sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)


# ── ADMIN: COURSES ───────────────────────────────────────

@app.get('/admin/courses')
def list_courses(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    items = [clean(i) for i in tbl('courses').scan()['Items']]
    return sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)

@app.post('/admin/courses')
def create_course(course: CourseIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('courses').put_item(Item={
        'id': str(uuid4()),
        'title': course.title,
        'description': course.description or '',
        'level': course.level or '',
        'stars': course.stars or 1,
        'depth': course.depth or '',
        'suspended': 0,
        'archived': 0,
        'created_at': now_iso(),
    })
    return {"status": "ok"}

@app.put('/admin/courses/{course_id}')
def update_course(course_id: str, course: CourseIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('courses').update_item(
        Key={'id': course_id},
        UpdateExpression='SET title=:t, description=:d, #lv=:l, stars=:s, depth=:dp',
        ExpressionAttributeNames={'#lv': 'level'},
        ExpressionAttributeValues={
            ':t': course.title, ':d': course.description or '',
            ':l': course.level or '', ':s': course.stars or 1, ':dp': course.depth or '',
        }
    )
    return {"status": "ok"}

@app.post('/admin/courses/{course_id}/suspend')
def suspend_course(course_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('courses').update_item(Key={'id': course_id},
        UpdateExpression='SET suspended=:v', ExpressionAttributeValues={':v': 1})
    return {"status": "ok"}

@app.post('/admin/courses/{course_id}/archive')
def archive_course(course_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('courses').update_item(Key={'id': course_id},
        UpdateExpression='SET archived=:v', ExpressionAttributeValues={':v': 1})
    return {"status": "ok"}

@app.post('/admin/courses/{course_id}/restore')
def restore_course(course_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('courses').update_item(Key={'id': course_id},
        UpdateExpression='SET suspended=:s, archived=:a',
        ExpressionAttributeValues={':s': 0, ':a': 0})
    return {"status": "ok"}

@app.delete('/admin/courses/{course_id}')
def delete_course(course_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('courses').delete_item(Key={'id': course_id})
    return {"status": "ok"}


# ── ADMIN: CONTACTS & BOOKINGS ───────────────────────────

@app.get('/admin/contacts')
def list_contacts(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    items = [clean(i) for i in tbl('contacts').scan()['Items']]
    return sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)

@app.get('/admin/bookings')
def list_bookings(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    items = [clean(i) for i in tbl('bookings').scan()['Items']]
    return sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)


# ── ADMIN: TESTIMONIALS ──────────────────────────────────

@app.get('/admin/testimonials')
def list_testimonials(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    items = [clean(i) for i in tbl('testimonials').scan()['Items']]
    return sorted(items, key=lambda x: (int(x.get('sort_order', 0)), x.get('id', '')))

@app.post('/admin/testimonials')
def create_testimonial(item: TestimonialIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('testimonials').put_item(Item={
        'id': str(uuid4()), 'name': item.name, 'location': item.location or '',
        'quote': item.quote, 'stars': item.stars or 5, 'sort_order': item.sort_order or 0,
        'enabled': 1, 'created_at': now_iso(),
    })
    return {"status": "ok"}

@app.put('/admin/testimonials/{item_id}')
def update_testimonial(item_id: str, item: TestimonialIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('testimonials').update_item(
        Key={'id': item_id},
        UpdateExpression='SET #n=:n, #loc=:l, quote=:q, stars=:s, sort_order=:o',
        ExpressionAttributeNames={'#n': 'name', '#loc': 'location'},
        ExpressionAttributeValues={
            ':n': item.name, ':l': item.location or '',
            ':q': item.quote, ':s': item.stars or 5, ':o': item.sort_order or 0,
        }
    )
    return {"status": "ok"}

@app.post('/admin/testimonials/{item_id}/toggle')
def toggle_testimonial(item_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    row = tbl('testimonials').get_item(Key={'id': item_id}).get('Item')
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    tbl('testimonials').update_item(Key={'id': item_id},
        UpdateExpression='SET enabled=:v',
        ExpressionAttributeValues={':v': 0 if int(row.get('enabled', 1)) else 1})
    return {"status": "ok"}

@app.delete('/admin/testimonials/{item_id}')
def delete_testimonial(item_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('testimonials').delete_item(Key={'id': item_id})
    return {"status": "ok"}


# ── ADMIN: GALLERY ───────────────────────────────────────

@app.get('/admin/gallery')
def list_gallery(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    items = [clean(i) for i in tbl('gallery').scan()['Items']]
    return sorted(items, key=lambda x: (int(x.get('sort_order', 0)), x.get('id', '')))

@app.post('/admin/gallery')
def create_gallery_item(item: GalleryItemIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('gallery').put_item(Item={
        'id': str(uuid4()), 'icon': item.icon or '🤿', 'caption': item.caption or '',
        'sort_order': item.sort_order or 0, 'enabled': 1, 'created_at': now_iso(),
    })
    return {"status": "ok"}

@app.put('/admin/gallery/{item_id}')
def update_gallery_item(item_id: str, item: GalleryItemIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('gallery').update_item(
        Key={'id': item_id},
        UpdateExpression='SET icon=:i, caption=:c, sort_order=:o',
        ExpressionAttributeValues={':i': item.icon or '🤿', ':c': item.caption or '', ':o': item.sort_order or 0}
    )
    return {"status": "ok"}

@app.post('/admin/gallery/{item_id}/toggle')
def toggle_gallery_item(item_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    row = tbl('gallery').get_item(Key={'id': item_id}).get('Item')
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    tbl('gallery').update_item(Key={'id': item_id},
        UpdateExpression='SET enabled=:v',
        ExpressionAttributeValues={':v': 0 if int(row.get('enabled', 1)) else 1})
    return {"status": "ok"}

@app.delete('/admin/gallery/{item_id}')
def delete_gallery_item(item_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('gallery').delete_item(Key={'id': item_id})
    return {"status": "ok"}


# ── ADMIN: FAQ ───────────────────────────────────────────

@app.get('/admin/faq')
def list_faq(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    items = [clean(i) for i in tbl('faq').scan()['Items']]
    return sorted(items, key=lambda x: (int(x.get('sort_order', 0)), x.get('id', '')))

@app.post('/admin/faq')
def create_faq(item: FAQItemIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('faq').put_item(Item={
        'id': str(uuid4()), 'question': item.question, 'answer': item.answer,
        'sort_order': item.sort_order or 0, 'enabled': 1, 'created_at': now_iso(),
    })
    return {"status": "ok"}

@app.put('/admin/faq/{item_id}')
def update_faq(item_id: str, item: FAQItemIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('faq').update_item(
        Key={'id': item_id},
        UpdateExpression='SET question=:q, answer=:a, sort_order=:o',
        ExpressionAttributeValues={':q': item.question, ':a': item.answer, ':o': item.sort_order or 0}
    )
    return {"status": "ok"}

@app.post('/admin/faq/{item_id}/toggle')
def toggle_faq(item_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    row = tbl('faq').get_item(Key={'id': item_id}).get('Item')
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    tbl('faq').update_item(Key={'id': item_id},
        UpdateExpression='SET enabled=:v',
        ExpressionAttributeValues={':v': 0 if int(row.get('enabled', 1)) else 1})
    return {"status": "ok"}

@app.delete('/admin/faq/{item_id}')
def delete_faq(item_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('faq').delete_item(Key={'id': item_id})
    return {"status": "ok"}


# ── ADMIN: LOCATIONS ─────────────────────────────────────

@app.get('/admin/locations')
def list_locations(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    items = [clean(i) for i in tbl('locations').scan()['Items']]
    return sorted(items, key=lambda x: (int(x.get('sort_order', 0)), x.get('id', '')))

@app.post('/admin/locations')
def create_location(item: LocationIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('locations').put_item(Item={
        'id': str(uuid4()), 'flag': item.flag or '', 'name': item.name,
        'description': item.description or '', 'sort_order': item.sort_order or 0,
        'enabled': 1, 'created_at': now_iso(),
    })
    return {"status": "ok"}

@app.put('/admin/locations/{item_id}')
def update_location(item_id: str, item: LocationIn, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('locations').update_item(
        Key={'id': item_id},
        UpdateExpression='SET flag=:f, #n=:n, description=:d, sort_order=:o',
        ExpressionAttributeNames={'#n': 'name'},
        ExpressionAttributeValues={
            ':f': item.flag or '', ':n': item.name,
            ':d': item.description or '', ':o': item.sort_order or 0,
        }
    )
    return {"status": "ok"}

@app.post('/admin/locations/{item_id}/toggle')
def toggle_location(item_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    row = tbl('locations').get_item(Key={'id': item_id}).get('Item')
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    tbl('locations').update_item(Key={'id': item_id},
        UpdateExpression='SET enabled=:v',
        ExpressionAttributeValues={':v': 0 if int(row.get('enabled', 1)) else 1})
    return {"status": "ok"}

@app.delete('/admin/locations/{item_id}')
def delete_location(item_id: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    tbl('locations').delete_item(Key={'id': item_id})
    return {"status": "ok"}


# ── ADMIN: SECTIONS ──────────────────────────────────────

@app.get('/admin/sections')
def list_sections(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    return [clean(i) for i in tbl('sections').scan()['Items']]

@app.post('/admin/sections/{key}/toggle')
def toggle_section(key: str, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    row = tbl('sections').get_item(Key={'key': key}).get('Item')
    if not row:
        raise HTTPException(status_code=404, detail="Section not found")
    tbl('sections').update_item(Key={'key': key},
        UpdateExpression='SET enabled=:v',
        ExpressionAttributeValues={':v': 0 if int(row.get('enabled', 1)) else 1})
    return {"status": "ok"}


# ── SEO / UTILS ──────────────────────────────────────────

@app.get('/sitemap.xml', response_class=PlainTextResponse)
def sitemap():
    host = os.getenv('SITE_HOST', 'https://example.com')
    pages = ["/", "/courses", "/about", "/faq"]
    for item in tbl('courses').scan(FilterExpression=Attr('archived').eq(0))['Items']:
        pages.append(f"/courses/{item['id']}")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for p in pages:
        xml += f"  <url><loc>{host}{p}</loc></url>\n"
    xml += "</urlset>"
    return xml

@app.get('/robots.txt', response_class=PlainTextResponse)
def robots():
    host = os.getenv('SITE_HOST', 'https://example.com')
    return f"User-agent: *\nAllow: /\nSitemap: {host}/sitemap.xml\n"


# ── FRONTEND ─────────────────────────────────────────────
# Works both locally (frontend/ is two levels up) and in Lambda (frontend/ copied alongside code)

_here = Path(__file__).resolve().parent
FRONTEND_DIR = (_here / "frontend") if (_here / "frontend").exists() else (_here.parent / "frontend")

@app.get("/", response_class=HTMLResponse)
def serve_index():
    return HTMLResponse(content=(FRONTEND_DIR / "index.html").read_text(), status_code=200)

@app.get("/admin.html", response_class=HTMLResponse)
def serve_admin():
    return HTMLResponse(content=(FRONTEND_DIR / "admin.html").read_text(), status_code=200)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

handler = Mangum(app, lifespan="off")
