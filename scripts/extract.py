import sys
from pathlib import Path

import pandas as pd

from sources import nepaltechhub, fatafatsewa

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT = BASE_DIR / "data" / "raw" / "phones.csv"

RUN_FATFAT = True

print("Scraping NepalTechHub...")
try:
    nth_rows = nepaltechhub.scrape()
except Exception as e:
    print(f"NepalTechHub failed: {e}")
    nth_rows = []

ffs_rows = []

if RUN_FATFAT:
    print("Scraping FatafatSewa...")
    try:
        ffs_rows = fatafatsewa.scrape()
    except Exception as e:
        print(f"FatafatSewa failed: {e}")

rows = nth_rows + ffs_rows

if not rows:
    sys.exit("No rows scraped")

df = pd.DataFrame(rows)

df = df.drop_duplicates(subset=["source", "url"])

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)

print(f"Saved {len(df)} rows")
print(df.groupby("source").size())