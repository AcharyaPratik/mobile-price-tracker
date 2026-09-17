"""
Load cleaned CSV into PostgreSQL.

Input:  data/processed/phones_clean.csv
Output: rows inserted into the mobile_prices table

Run from project root:
    python scripts/load.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# ── resolve paths relative to project root ───────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEAN_PATH   = PROJECT_ROOT / "data" / "processed" / "phones_clean.csv"
SCHEMA_PATH  = PROJECT_ROOT / "sql" / "schema.sql"

load_dotenv(PROJECT_ROOT / ".env")

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "mobile_tracker"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_conn():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to Postgres: {e}")
        print("   Check .env credentials and that Postgres is running.")
        sys.exit(1)


def apply_schema(conn) -> None:
    if not SCHEMA_PATH.exists():
        print(f"⚠️  No schema.sql at {SCHEMA_PATH}")
        return
    sql = SCHEMA_PATH.read_text().strip()
    if not sql:
        print(f"❌ {SCHEMA_PATH} is empty — write the CREATE TABLE there")
        sys.exit(1)
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"✅ Applied schema from {SCHEMA_PATH.name}")

def load_csv(conn) -> int:
    """Insert every row from the cleaned CSV. Returns rows attempted."""
    if not CLEAN_PATH.exists():
        print(f"❌ Cleaned CSV not found: {CLEAN_PATH}")
        print("   Run transform.py first.")
        sys.exit(1)

    df = pd.read_csv(CLEAN_PATH)
    print(f"→ Loaded {len(df)} rows from {CLEAN_PATH.name}")

    df["scraped_at"] = pd.to_datetime(df["scraped_at"])

    records = [
        (
            row.source,
            row.name,
            row.brand,
            int(row.price),
            row.price_category,
            row.url,
            row.scraped_at.to_pydatetime(),
        )
        for row in df.itertuples(index=False)
    ]

    insert_sql = """
        INSERT INTO mobile_prices
            (source, name, brand, price, price_category, url, scraped_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source, url) DO NOTHING
    """

    with conn.cursor() as cur:
        execute_batch(cur, insert_sql, records, page_size=200)
        inserted = cur.rowcount
    conn.commit()
    return inserted


def verify(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM mobile_prices")
        total = cur.fetchone()[0]

        cur.execute("""
            SELECT source, COUNT(*) FROM mobile_prices
            GROUP BY source ORDER BY source
        """)
        by_source = cur.fetchall()

        cur.execute("""
            SELECT brand, COUNT(*) FROM mobile_prices
            GROUP BY brand ORDER BY COUNT(*) DESC LIMIT 5
        """)
        top_brands = cur.fetchall()

        cur.execute("SELECT MIN(price), ROUND(AVG(price)), MAX(price) FROM mobile_prices")
        min_p, avg_p, max_p = cur.fetchone()

    print(f"\n📊 Database summary:")
    print(f"   total rows: {total}")
    print(f"\n   by source:")
    for src, n in by_source:
        print(f"     {src:15s} {n:>5}")
    print(f"\n   top 5 brands:")
    for b, n in top_brands:
        print(f"     {b:15s} {n:>5}")
    print(f"\n   price range:  min {min_p:,.0f}  |  avg {avg_p:,.0f}  |  max {max_p:,.0f}")


def main() -> None:
    conn = get_conn()
    try:
        apply_schema(conn)
        inserted = load_csv(conn)
        print(f"✅ Inserted {inserted} new rows")
        verify(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()