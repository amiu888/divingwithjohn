import os
from uuid import uuid4
from datetime import datetime, timezone
from dotenv import load_dotenv
import boto3

load_dotenv()

def get_dynamodb():
    kwargs = {'region_name': os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')
    if endpoint_url:
        kwargs['endpoint_url'] = endpoint_url
        kwargs['aws_access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID', 'local')
        kwargs['aws_secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY', 'local')
    return boto3.resource('dynamodb', **kwargs)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

TABLES = [
    ('dwj_contacts',     'id',    'S'),
    ('dwj_courses',      'id',    'S'),
    ('dwj_bookings',     'id',    'S'),
    ('dwj_users',        'email', 'S'),
    ('dwj_testimonials', 'id',    'S'),
    ('dwj_gallery',      'id',    'S'),
    ('dwj_faq',          'id',    'S'),
    ('dwj_locations',    'id',    'S'),
    ('dwj_sections',     'key',   'S'),
]

def create_tables(ddb):
    client = ddb.meta.client
    existing = {t for t in client.list_tables()['TableNames']}
    for table_name, pk_name, pk_type in TABLES:
        if table_name not in existing:
            ddb.create_table(
                TableName=table_name,
                AttributeDefinitions=[{'AttributeName': pk_name, 'AttributeType': pk_type}],
                KeySchema=[{'AttributeName': pk_name, 'KeyType': 'HASH'}],
                BillingMode='PAY_PER_REQUEST',
            )
            print(f"  Created: {table_name}")
        else:
            print(f"  Exists:  {table_name}")

def seed_data(ddb):
    sections_table = ddb.Table('dwj_sections')
    if not sections_table.scan()['Items']:
        for key, label in [
            ('hero',         'Hero Banner'),
            ('about',        'About'),
            ('courses',      'Courses'),
            ('locations',    'Our Dive Sites'),
            ('process',      'How It Works'),
            ('testimonials', 'Testimonials'),
            ('gallery',      'Gallery'),
            ('faq',          'FAQ'),
            ('contact',      'Contact'),
        ]:
            sections_table.put_item(Item={'key': key, 'label': label, 'enabled': 1})
        print("  Seeded sections")

    t_table = ddb.Table('dwj_testimonials')
    if not t_table.scan()['Items']:
        for name, location, quote, stars, sort_order in [
            ("Maria R.", "São Paulo, Brazil", "John's calm and methodical teaching style made me feel completely safe in the water. I went from zero experience to AIDA 2 certified in one week. Incredible!", 5, 1),
            ("James K.", "London, UK", "I was terrified of deep water before this course. John's patience and expert instruction transformed my relationship with the ocean. Truly life-changing.", 5, 2),
            ("Sofia C.", "Barcelona, Spain", "The Bali course was outstanding. World-class instruction at a world-class location. I hit 30m on my final dive — something I never imagined possible.", 5, 3),
            ("Aisha P.", "Dubai, UAE", "Booked the kids camp for my two children (9 and 12). They absolutely loved every session and now can't stop talking about getting their Junior AIDA cert. Thank you John!", 5, 4),
            ("Luca N.", "Sydney, Australia", "Did the AIDA 3 advanced course in Dahab. John's 1-on-1 technique coaching is on another level — he spotted and fixed an equalisation issue that had been holding me back for years.", 5, 5),
            ("Priya V.", "Mumbai, India", "From the booking process to the final dive, everything was seamless. John clearly loves what he does and that passion is contagious. Already booked my Level 3!", 5, 6),
        ]:
            t_table.put_item(Item={
                'id': str(uuid4()), 'name': name, 'location': location,
                'quote': quote, 'stars': stars, 'sort_order': sort_order,
                'enabled': 1, 'created_at': now_iso(),
            })
        print("  Seeded testimonials")

    g_table = ddb.Table('dwj_gallery')
    if not g_table.scan()['Items']:
        for icon, caption, sort_order in [
            ('🤿', 'Open water freediving session', 1),
            ('🌊', 'Ocean training conditions', 2),
            ('🐠', 'Reef exploration dive', 3),
            ('🏊', 'Pool technique session', 4),
            ('🐋', 'Pelagic encounter', 5),
            ('🐬', 'Group freediving day', 6),
        ]:
            g_table.put_item(Item={
                'id': str(uuid4()), 'icon': icon, 'caption': caption,
                'sort_order': sort_order, 'enabled': 1, 'created_at': now_iso(),
            })
        print("  Seeded gallery")

    faq_table = ddb.Table('dwj_faq')
    if not faq_table.scan()['Items']:
        for question, answer, sort_order in [
            ("Do I need to know how to swim to take a freediving course?", "Yes — basic swimming ability is required. You should be comfortable in the water and able to swim at least 200m without stopping. You don't need to be a strong swimmer, just comfortable.", 1),
            ("What equipment do I need to bring?", "All essential equipment — mask, fins, wetsuit, and safety lanyard — is provided as part of your course. Just bring a swimsuit, sunscreen, and a towel. If you have your own gear you're welcome to use it.", 2),
            ("Is freediving safe?", "Freediving is very safe when practised correctly with a trained buddy and an experienced instructor. All our courses cover safety protocols in depth. We follow AIDA's strict safety standards and never dive alone.", 3),
            ("How long does certification take?", "AIDA Level 1 takes 2 days. Level 2 takes 3 days. Level 3 is a 4-day intensive programme. All timelines include both theory and in-water sessions.", 4),
            ("What is the minimum age for courses?", "Adults (18+) can join all AIDA courses. Our Junior Ocean Explorers programme is designed for children aged 8–16 with dedicated lifeguard supervision throughout every session.", 5),
            ("Can I book a private lesson?", "Absolutely. Private and small-group instruction is available for all levels. Just mention your preference in the contact form and we'll put together a tailored programme for you.", 6),
        ]:
            faq_table.put_item(Item={
                'id': str(uuid4()), 'question': question, 'answer': answer,
                'sort_order': sort_order, 'enabled': 1, 'created_at': now_iso(),
            })
        print("  Seeded FAQ")

    loc_table = ddb.Table('dwj_locations')
    if not loc_table.scan()['Items']:
        for flag, name, description, sort_order in [
            ('🇮🇩', 'Bali, Indonesia', 'Crystal-clear waters, vibrant reefs, and world-famous dive sites like Tulamben and Nusa Penida.', 1),
            ('🇪🇬', 'Dahab, Egypt', 'Legendary Blue Hole and canyon dives in the Red Sea — a freediving mecca with warm, calm conditions.', 2),
            ('🇹🇭', 'Koh Tao, Thailand', 'Exceptional visibility and gentle currents make this island paradise perfect for all skill levels.', 3),
            ('🇮🇳', 'Goa, India', 'Warm Arabian Sea waters with diverse marine life and beginner-friendly conditions year-round.', 4),
            ('🇵🇹', 'Azores, Portugal', 'Atlantic pelagic dives — swim with dolphins, whale sharks, and manta rays in the open ocean.', 5),
        ]:
            loc_table.put_item(Item={
                'id': str(uuid4()), 'flag': flag, 'name': name,
                'description': description, 'sort_order': sort_order,
                'enabled': 1, 'created_at': now_iso(),
            })
        print("  Seeded locations")

if __name__ == '__main__':
    ddb = get_dynamodb()
    print("Creating tables...")
    create_tables(ddb)
    print("Seeding data...")
    seed_data(ddb)
    print("Done!")
