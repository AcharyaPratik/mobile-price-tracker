import os
import sys
import pandas as pd
from pathlib import Path

from sources import nepaltechhub, fatafatsewa

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = PROJECT_ROOT / "data" / "raw" / "phones.csv"

COLUMNS = [
    "source", "source_id", "name", "brand",
    "price_raw", "price_npr", "status", "url", "scraped_at",
]

# Flip to False to skip Fatafat if Playwright isn't installed.
RUN_FATFAT = True


def run_nepaltechhub() -> list[dict]:
    print("▶ Scraping NepalTechHub (all pages)...")
    try:
        rows = nepaltechhub.scrape()
        print(f"  ✅ nepaltechhub: {len(rows)} rows\n")
        return rows
    except Exception as e:
        print(f"  ❌ nepaltechhub failed: {e}\n")
        return []


def run_fatafatsewa() -> list[dict]:
    if not RUN_FATFAT:
        print("▶ Skipping Fatafat Sewa (RUN_FATFAT=False)\n")
        return []

    print("▶ Scraping Fatafat Sewa (Playwright, all pages)...")
    try:
        rows = fatafatsewa.scrape()
        print(f"  ✅ fatafatsewa: {len(rows)} rows\n")
        return rows
    except ImportError:
        print("  ❌ Playwright not installed. Run:")
        print("       pip install playwright && playwright install chromium\n")
        return []
    except Exception as e:
        print(f"  ❌ fatafatsewa failed: {e}\n")
        return []


def main() -> None:
    nth_rows = run_nepaltechhub()
    ffs_rows = run_fatafatsewa()
    all_rows = nth_rows + ffs_rows

    if not all_rows:
        print("❌ No rows scraped from any source.")
        sys.exit(1)

    df = pd.DataFrame(all_rows)[COLUMNS]

    # de-dupe within each source (same site + same URL = true dup)
    before = len(df)
    df = df.drop_duplicates(subset=["source", "url"])
    dupes = before - len(df)
    if dupes:
        print(f"ℹ️  Removed {dupes} in-source duplicates")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)

    print(f"✅ Saved {len(df)} rows → {OUTPUT}")
    print("\nBreakdown by source:")
    print(df.groupby("source").size().to_string())


if __name__ == "__main__":
    main()