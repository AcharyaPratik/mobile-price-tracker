import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "mobile_tracker"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

conn = psycopg2.connect(**DB_CONFIG)

with conn.cursor() as cur:

    cur.execute("""
        DELETE FROM price_history
        WHERE snapshot_date = CURRENT_DATE
    """)

    deleted = cur.rowcount

    cur.execute("""
        INSERT INTO price_history
        (
            source,
            url,
            name,
            brand,
            price,
            snapshot_date,
            captured_at
        )
        SELECT
            source,
            url,
            name,
            brand,
            price,
            CURRENT_DATE,
            NOW()
        FROM mobile_prices
    """)

    inserted = cur.rowcount

    cur.execute("""
        SELECT COUNT(DISTINCT snapshot_date)
        FROM price_history
    """)

    days = cur.fetchone()[0]

conn.commit()
conn.close()

print("Snapshot complete")
print(f"Deleted: {deleted}")
print(f"Inserted: {inserted}")
print(f"Days tracked: {days}")