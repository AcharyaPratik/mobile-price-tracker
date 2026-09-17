import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_batch

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

CLEAN_PATH = BASE_DIR / "data" / "processed" / "phones_clean.csv"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", 5432),
    dbname=os.getenv("DB_NAME", "mobile_tracker"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD"),
)

print("Reading cleaned data...")
df = pd.read_csv(CLEAN_PATH)

with conn.cursor() as cur:

    print("Applying schema...")
    schema_sql = SCHEMA_PATH.read_text()

    # Strip psql meta-commands (lines starting with \) — psycopg2 can't parse them
    schema_sql = "\n".join(
        line for line in schema_sql.splitlines()
        if not line.lstrip().startswith("\\")
    )

    cur.execute(schema_sql)

    records = [
        (
            row.source,
            row.name,
            row.brand,
            int(row.price),
            row.price_category,
            row.url,
            pd.to_datetime(row.scraped_at),
        )
        for row in df.itertuples(index=False)
    ]

    print("Loading data...")

    execute_batch(
        cur,
        """
        INSERT INTO mobile_prices
        (
            source,
            name,
            brand,
            price,
            price_category,
            url,
            scraped_at
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (source, url) DO NOTHING
        """,
        records,
        page_size=200,
    )

conn.commit()

with conn.cursor() as cur:

    cur.execute("SELECT COUNT(*) FROM mobile_prices")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT source, COUNT(*)
        FROM mobile_prices
        GROUP BY source
        ORDER BY source
    """)
    sources = cur.fetchall()

print(f"\nTotal rows: {total}")

print("\nRows by source:")
for source, count in sources:
    print(f"  {source}: {count}")

conn.close()

print("\nLoad complete.")