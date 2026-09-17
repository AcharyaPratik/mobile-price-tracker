"""
Generate a price-change report from price_history.

Compares today's snapshot to the most recent prior snapshot
and writes reports/price_drops.csv.

Run: python scripts/report.py
"""

import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "mobile_tracker"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


QUERY = """
WITH latest AS (
    SELECT MAX(snapshot_date) AS d FROM price_history
),
prior AS (
    SELECT MAX(snapshot_date) AS d
    FROM price_history
    WHERE snapshot_date < (SELECT d FROM latest)
)
SELECT
    t.brand,
    t.name,
    y.price                     AS old_price,
    t.price                     AS new_price,
    t.price - y.price           AS change,
    ROUND(100.0 * (t.price - y.price) / y.price, 2) AS pct_change,
    t.source,
    t.url,
    y.snapshot_date             AS from_date,
    t.snapshot_date             AS to_date
FROM      price_history t
JOIN      price_history y ON y.url = t.url
WHERE t.snapshot_date = (SELECT d FROM latest)
  AND y.snapshot_date = (SELECT d FROM prior)
  AND t.price <> y.price
ORDER BY ABS(t.price - y.price) DESC
"""


def main() -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        df = pd.read_sql(QUERY, conn)
    finally:
        conn.close()

    if df.empty:
        print("ℹ️  No price changes yet (need at least two snapshot days).")
        print("   Run the DAG on two different days, or use the fake-yesterday trick.")
        return

    drops = df[df["change"] < 0].copy()
    rises = df[df["change"] > 0].copy()

    drops.to_csv(REPORTS_DIR / "price_drops.csv",   index=False)
    rises.to_csv(REPORTS_DIR / "price_rises.csv",   index=False)
    df.to_csv(   REPORTS_DIR / "price_changes.csv", index=False)

    print(f"✅ Report generated")
    print(f"   rows with price drops:  {len(drops)}")
    print(f"   rows with price rises:  {len(rises)}")
    print(f"   written to:             {REPORTS_DIR}")
    print()

    if not drops.empty:
        print("── Top 10 price drops ─────────────────────────────")
        for _, r in drops.head(10).iterrows():
            print(f"  {r['brand']:12s} {r['name'][:40]:40s} "
                  f"{int(r['old_price']):>8,} → {int(r['new_price']):>8,}  "
                  f"({int(r['change']):+,})")
    else:
        print("(no price drops today)")


if __name__ == "__main__":
    main()