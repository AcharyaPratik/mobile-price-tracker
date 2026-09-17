"""
Snapshot the current mobile_prices table into price_history.

One row per (source, url, snapshot_date). Re-running on the same day
updates today's row instead of inserting a duplicate.

Run: python scripts/snapshot.py
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "mobile_tracker"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def main() -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            # delete today's existing snapshot (idempotent re-runs)
            cur.execute("""
                DELETE FROM price_history
                WHERE snapshot_date = CURRENT_DATE
            """)
            deleted = cur.rowcount

            # copy current state into history
            cur.execute("""
                INSERT INTO price_history
                    (source, url, name, brand, price, snapshot_date, captured_at)
                SELECT source, url, name, brand, price, CURRENT_DATE, NOW()
                FROM mobile_prices
            """)
            inserted = cur.rowcount

            # summary
            cur.execute("SELECT COUNT(DISTINCT snapshot_date) FROM price_history")
            days = cur.fetchone()[0]

        conn.commit()

        print(f"✅ Snapshot complete")
        print(f"   deleted (today, previous run): {deleted}")
        print(f"   inserted (today):              {inserted}")
        print(f"   total distinct days tracked:   {days}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
