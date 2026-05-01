"""
ElectaVerse — Database Seed Script
Populates the database with constituencies and booths.
All data is seeded from here — nothing hardcoded in the application.

Usage:
    python db/seed.py
"""

import sys
import os
import random
import mysql.connector

# Add parent dir to path so we can import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# ─────────────────────────────────────────────
# Constituency data — the ONLY source of truth
# ─────────────────────────────────────────────
CONSTITUENCIES = [
    {'id': 'NDL', 'name': 'New Delhi', 'state': 'Delhi', 'lat': 28.6139, 'lng': 77.2090},
    {'id': 'MBN', 'name': 'Mumbai North', 'state': 'Maharashtra', 'lat': 19.1760, 'lng': 72.8777},
    {'id': 'BLS', 'name': 'Bangalore South', 'state': 'Karnataka', 'lat': 12.9352, 'lng': 77.6245},
    {'id': 'CHC', 'name': 'Chennai Central', 'state': 'Tamil Nadu', 'lat': 13.0827, 'lng': 80.2707},
    {'id': 'KLN', 'name': 'Kolkata North', 'state': 'West Bengal', 'lat': 22.6128, 'lng': 88.3630},
    {'id': 'HYD', 'name': 'Hyderabad', 'state': 'Telangana', 'lat': 17.3850, 'lng': 78.4867},
    {'id': 'PNE', 'name': 'Pune', 'state': 'Maharashtra', 'lat': 18.5204, 'lng': 73.8567},
    {'id': 'LKW', 'name': 'Lucknow', 'state': 'Uttar Pradesh', 'lat': 26.8467, 'lng': 80.9462},
    {'id': 'JPR', 'name': 'Jaipur Rural', 'state': 'Rajasthan', 'lat': 26.9124, 'lng': 75.7873},
    {'id': 'AHE', 'name': 'Ahmedabad East', 'state': 'Gujarat', 'lat': 23.0225, 'lng': 72.5714},
]

BOOTHS_PER_CONSTITUENCY = 20  # 200 total booths


def create_database():
    """Create the database if it doesn't exist."""
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS electaverse")
    cursor.close()
    conn.close()
    print("✅ Database 'electaverse' ensured.")


def run_schema():
    """Execute the schema SQL file."""
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
    )
    cursor = conn.cursor()
    for statement in schema_sql.split(';'):
        stmt = statement.strip()
        if stmt:
            try:
                cursor.execute(stmt)
            except mysql.connector.Error as e:
                # Skip non-critical errors (e.g., duplicate key on re-run)
                if e.errno not in (1061, 1062):  # Duplicate key/index
                    print(f"  ⚠️  {e.msg}")
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Schema applied.")


def seed_constituencies():
    """Insert constituency master data."""
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
    )
    cursor = conn.cursor()

    for c in CONSTITUENCIES:
        cursor.execute(
            """INSERT INTO constituencies (id, name, state, lat, lng)
               VALUES (%s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE name=VALUES(name)""",
            (c['id'], c['name'], c['state'], c['lat'], c['lng'])
        )

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {len(CONSTITUENCIES)} constituencies seeded.")


def seed_booths():
    """Generate and insert booths across all constituencies."""
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
    )
    cursor = conn.cursor()

    booth_count = 0
    for c in CONSTITUENCIES:
        for i in range(1, BOOTHS_PER_CONSTITUENCY + 1):
            booth_id = f"BOOTH-{c['id']}-{i:03d}"
            booth_name = f"{c['name']} Booth #{i}"
            lat = round(c['lat'] + random.uniform(-0.08, 0.08), 4)
            lng = round(c['lng'] + random.uniform(-0.08, 0.08), 4)
            registered = random.randint(800, 1500)
            throughput = round(25 + random.uniform(-5, 5), 1)

            cursor.execute(
                """INSERT INTO booths (id, name, constituency_id, lat, lng, registered_voters, base_throughput)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE name=VALUES(name)""",
                (booth_id, booth_name, c['id'], lat, lng, registered, throughput)
            )
            booth_count += 1

    # Update total registered voters per constituency
    cursor.execute("""
        UPDATE constituencies c
        SET total_registered_voters = (
            SELECT COALESCE(SUM(registered_voters), 0) FROM booths WHERE constituency_id = c.id
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {booth_count} booths seeded across {len(CONSTITUENCIES)} constituencies.")


def verify():
    """Verify the seed by printing summary stats."""
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as count FROM constituencies")
    print(f"\n📊 Constituencies: {cursor.fetchone()['count']}")

    cursor.execute("SELECT COUNT(*) as count FROM booths")
    print(f"📊 Booths: {cursor.fetchone()['count']}")

    cursor.execute("SELECT SUM(registered_voters) as total FROM booths")
    total = cursor.fetchone()['total']
    print(f"📊 Total registered voters: {total:,}")

    cursor.execute("SELECT COUNT(*) as count FROM simulation_config")
    print(f"📊 Simulation config entries: {cursor.fetchone()['count']}")

    cursor.execute("SELECT COUNT(*) as count FROM incident_config")
    print(f"📊 Incident config entries: {cursor.fetchone()['count']}")

    cursor.execute("SELECT COUNT(*) as count FROM peak_multipliers")
    print(f"📊 Peak multiplier entries: {cursor.fetchone()['count']}")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    print("🗳️  ElectaVerse — Database Seeding\n")
    create_database()
    run_schema()
    seed_constituencies()
    seed_booths()
    verify()
    print("\n✅ Seeding complete! Database is ready.")
