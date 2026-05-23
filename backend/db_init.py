import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "divingwithjohn.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, description TEXT, level TEXT,
        stars INTEGER DEFAULT 1, depth TEXT,
        suspended INTEGER DEFAULT 0, archived INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER, user_email TEXT, date TEXT,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE, name TEXT, provider TEXT, provider_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS seo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page TEXT UNIQUE, title TEXT, description TEXT,
        og_title TEXT, og_description TEXT, og_image TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS testimonials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, location TEXT, quote TEXT NOT NULL,
        stars INTEGER DEFAULT 5, enabled INTEGER DEFAULT 1,
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS gallery_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        icon TEXT DEFAULT '🤿', caption TEXT,
        enabled INTEGER DEFAULT 1, sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS faq_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL, answer TEXT NOT NULL,
        enabled INTEGER DEFAULT 1, sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flag TEXT, name TEXT NOT NULL, description TEXT,
        enabled INTEGER DEFAULT 1, sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sections (
        key TEXT PRIMARY KEY,
        label TEXT NOT NULL,
        enabled INTEGER DEFAULT 1
    )''')

    conn.commit()

    # Seed sections (skip if already seeded)
    existing_sections = c.execute('SELECT COUNT(*) FROM sections').fetchone()[0]
    if not existing_sections:
        c.executemany('INSERT OR IGNORE INTO sections (key,label,enabled) VALUES (?,?,?)', [
            ('hero',         'Hero Banner',        1),
            ('about',        'About',              1),
            ('courses',      'Courses',            1),
            ('locations',    'Our Dive Sites',     1),
            ('process',      'How It Works',       1),
            ('testimonials', 'Testimonials',       1),
            ('gallery',      'Gallery',            1),
            ('faq',          'FAQ',                1),
            ('contact',      'Contact',            1),
        ])

    # Seed testimonials
    existing_t = c.execute('SELECT COUNT(*) FROM testimonials').fetchone()[0]
    if not existing_t:
        c.executemany(
            'INSERT INTO testimonials (name,location,quote,stars,sort_order) VALUES (?,?,?,?,?)',
            [
                ("Maria R.", "São Paulo, Brazil",
                 "John's calm and methodical teaching style made me feel completely safe in the water. I went from zero experience to AIDA 2 certified in one week. Incredible!",
                 5, 1),
                ("James K.", "London, UK",
                 "I was terrified of deep water before this course. John's patience and expert instruction transformed my relationship with the ocean. Truly life-changing.",
                 5, 2),
                ("Sofia C.", "Barcelona, Spain",
                 "The Bali course was outstanding. World-class instruction at a world-class location. I hit 30m on my final dive — something I never imagined possible.",
                 5, 3),
                ("Aisha P.", "Dubai, UAE",
                 "Booked the kids camp for my two children (9 and 12). They absolutely loved every session and now can't stop talking about getting their Junior AIDA cert. Thank you John!",
                 5, 4),
                ("Luca N.", "Sydney, Australia",
                 "Did the AIDA 3 advanced course in Dahab. John's 1-on-1 technique coaching is on another level — he spotted and fixed an equalisation issue that had been holding me back for years.",
                 5, 5),
                ("Priya V.", "Mumbai, India",
                 "From the booking process to the final dive, everything was seamless. John clearly loves what he does and that passion is contagious. Already booked my Level 3!",
                 5, 6),
            ]
        )

    # Seed gallery
    existing_g = c.execute('SELECT COUNT(*) FROM gallery_items').fetchone()[0]
    if not existing_g:
        c.executemany(
            'INSERT INTO gallery_items (icon,caption,sort_order) VALUES (?,?,?)',
            [
                ('🤿', 'Open water freediving session', 1),
                ('🌊', 'Ocean training conditions',     2),
                ('🐠', 'Reef exploration dive',         3),
                ('🏊', 'Pool technique session',        4),
                ('🐋', 'Pelagic encounter',             5),
                ('🐬', 'Group freediving day',          6),
            ]
        )

    # Seed FAQ
    existing_f = c.execute('SELECT COUNT(*) FROM faq_items').fetchone()[0]
    if not existing_f:
        c.executemany(
            'INSERT INTO faq_items (question,answer,sort_order) VALUES (?,?,?)',
            [
                ("Do I need to know how to swim to take a freediving course?",
                 "Yes — basic swimming ability is required. You should be comfortable in the water and able to swim at least 200m without stopping. You don't need to be a strong swimmer, just comfortable.",
                 1),
                ("What equipment do I need to bring?",
                 "All essential equipment — mask, fins, wetsuit, and safety lanyard — is provided as part of your course. Just bring a swimsuit, sunscreen, and a towel. If you have your own gear you're welcome to use it.",
                 2),
                ("Is freediving safe?",
                 "Freediving is very safe when practised correctly with a trained buddy and an experienced instructor. All our courses cover safety protocols in depth. We follow AIDA's strict safety standards and never dive alone.",
                 3),
                ("How long does certification take?",
                 "AIDA Level 1 takes 2 days. Level 2 takes 3 days. Level 3 is a 4-day intensive programme. All timelines include both theory and in-water sessions.",
                 4),
                ("What is the minimum age for courses?",
                 "Adults (18+) can join all AIDA courses. Our Junior Ocean Explorers programme is designed for children aged 8–16 with dedicated lifeguard supervision throughout every session.",
                 5),
                ("Can I book a private lesson?",
                 "Absolutely. Private and small-group instruction is available for all levels. Just mention your preference in the contact form and we'll put together a tailored programme for you.",
                 6),
            ]
        )

    # Seed locations
    existing_l = c.execute('SELECT COUNT(*) FROM locations').fetchone()[0]
    if not existing_l:
        c.executemany(
            'INSERT INTO locations (flag,name,description,sort_order) VALUES (?,?,?,?)',
            [
                ('🇮🇩', 'Bali, Indonesia',
                 'Crystal-clear waters, vibrant reefs, and world-famous dive sites like Tulamben and Nusa Penida.',
                 1),
                ('🇪🇬', 'Dahab, Egypt',
                 'Legendary Blue Hole and canyon dives in the Red Sea — a freediving mecca with warm, calm conditions.',
                 2),
                ('🇹🇭', 'Koh Tao, Thailand',
                 'Exceptional visibility and gentle currents make this island paradise perfect for all skill levels.',
                 3),
                ('🇮🇳', 'Goa, India',
                 'Warm Arabian Sea waters with diverse marine life and beginner-friendly conditions year-round.',
                 4),
                ('🇵🇹', 'Azores, Portugal',
                 'Atlantic pelagic dives — swim with dolphins, whale sharks, and manta rays in the open ocean.',
                 5),
            ]
        )

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print(f"Initialized DB at {DB_PATH}")
