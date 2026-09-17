import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "mobile_tracker"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

QUERY = """
WITH latest AS (
    SELECT MAX(snapshot_date) AS d
    FROM price_history
),
prior AS (
    SELECT MAX(snapshot_date) AS d
    FROM price_history
    WHERE snapshot_date < (SELECT d FROM latest)
)
SELECT
    t.brand,
    t.name,
    y.price AS old_price,
    t.price AS new_price,
    t.price - y.price AS change,
    ROUND(100.0 * (t.price - y.price) / y.price, 2) AS pct_change,
    t.source,
    t.url,
    y.snapshot_date AS from_date,
    t.snapshot_date AS to_date
FROM price_history t
JOIN price_history y
    ON y.url = t.url
WHERE t.snapshot_date = (SELECT d FROM latest)
  AND y.snapshot_date = (SELECT d FROM prior)
  AND t.price <> y.price
ORDER BY ABS(t.price - y.price) DESC
"""

conn = psycopg2.connect(**DB_CONFIG)

df = pd.read_sql(QUERY, conn)

conn.close()

if df.empty:
    print("No price changes found.")
    print("You need at least two snapshot dates.")
    raise SystemExit()

drops = df[df["change"] < 0]
rises = df[df["change"] > 0]

drops.to_csv(REPORTS_DIR / "price_drops.csv", index=False)
rises.to_csv(REPORTS_DIR / "price_rises.csv", index=False)
df.to_csv(REPORTS_DIR / "price_changes.csv", index=False)

print("Report generated")
print(f"Price drops : {len(drops)}")
print(f"Price rises : {len(rises)}")
print(f"Saved files : {REPORTS_DIR}")

if not drops.empty:

    print("\nTop 10 price drops\n")

    for _, row in drops.head(10).iterrows():
        print(
            f"{row['brand']:12s} "
            f"{row['name'][:40]:40s} "
            f"{int(row['old_price']):>8,} -> "
            f"{int(row['new_price']):>8,} "
            f"({int(row['change']):+,})"
        )