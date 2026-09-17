"""
Transform raw phone listings into a clean, Postgres-ready CSV.

Input:  data/raw/phones.csv
Output: data/processed/phones_clean.csv
"""

import os
import re
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "phones.csv"
CLEAN_PATH = PROJECT_ROOT / "data" / "processed" / "phones_clean.csv"

BRAND_MAP = {
    "apple":    "Apple",
    "samsung":  "Samsung",
    "xiaomi":   "Xiaomi",
    "redmi":    "Xiaomi",
    "poco":     "Poco",
    "oneplus":  "OnePlus",
    "oppo":     "Oppo",
    "vivo":     "Vivo",
    "realme":   "Realme",
    "honor":    "Honor",
    "huawei":   "Huawei",
    "motorola": "Motorola",
    "moto":     "Motorola",
    "nokia":    "Nokia",
    "nothing":  "Nothing",
    "infinix":  "Infinix",
    "tecno":    "Tecno",
    "itel":     "Itel",
    "zte":      "ZTE",
    "google":   "Google",
    "ai+":      "AI+",
    "ai":       "AI+",
}

# ── name cleaning ────────────────────────────────────────────────

def clean_name(name):
    if pd.isna(name):
        return ""

    name = str(name).strip()

    name = name.split("|")[0]
    name = re.split(r"\s+[Ww]ith\s+", name)[0]
    name = re.split(r"\s+[—–]\s+", name)[0]

    return re.sub(r"\s+", " ", name).strip()


# ── price parsing ────────────────────────────────────────────────

def parse_price(value):
    if pd.isna(value):
        return None

    digits = re.sub(r"[^\d]", "", str(value))

    return int(digits) if digits else None


# ── brand helpers ────────────────────────────────────────────────

def normalize_brand(value):
    if pd.isna(value):
        return ""

    value = str(value).strip().lower()

    return BRAND_MAP.get(value, value.title())


def derive_brand_from_name(name):
    if pd.isna(name):
        return ""

    first = str(name).split()[0]

    return BRAND_MAP.get(
        first.lower().rstrip(".,"),
        first.title()
    )


# ── main pipeline ────────────────────────────────────────────────

def transform() -> pd.DataFrame:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw CSV not found: {RAW_PATH}. Run extract.py first.")

    print(f"→ Reading {RAW_PATH}")
    df = pd.read_csv(RAW_PATH)
    print(f"  loaded {len(df)} raw rows")

    # ── 1. clean names ───────────────────────────────────────────
    df["name"] = df["name"].apply(clean_name)

    # ── 2. parse price ───────────────────────────────────────────
    df["price"] = df["price_npr"].apply(parse_price)
    df.loc[df["price"].isna(), "price"] = df["price_raw"].apply(parse_price)

    # ── 3. normalize brand ───────────────────────────────────────
    df["brand_clean"] = df["brand"].apply(normalize_brand)
    missing_brand = df["brand_clean"] == ""
    df.loc[missing_brand, "brand_clean"] = df.loc[missing_brand, "name"].apply(
        derive_brand_from_name
    )

    # ── 4. drop rows without a price ─────────────────────────────
    before = len(df)
    df = df[df["price"].notna()].copy()
    if before - len(df):
        print(f"  dropped {before - len(df)} rows with no parseable price")

    # ── 5. drop rows without a name ──────────────────────────────
    df = df[df["name"].astype(str).str.strip() != ""]

    # ── 6. price category bucket ─────────────────────────────────
    df["price_category"] = pd.cut(
        df["price"],
        bins=[0, 20_000, 40_000, 80_000, 150_000, float("inf")],
        labels=["budget", "mid-range", "upper-mid", "premium", "flagship"],
    ).astype(str)

    # ── 7. final columns (no status!) ────────────────────────────
    out = df[
        [
            "source",
            "name",
            "brand_clean",
            "price",
            "price_category",
            "url",
            "scraped_at",
        ]
    ]
    out.rename(
        columns={"brand_clean": "brand"},
        inplace=True
    )

    # ── 8. dedupe ────────────────────────────────────────────────
    before = len(out)
    out = out.drop_duplicates(subset=["source", "url"])
    if before - len(out):
        print(f"  removed {before - len(out)} duplicates")

    out = out.sort_values(["brand", "price"]).reset_index(drop=True)
    return out


def main() -> None:
    clean = transform()

    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(CLEAN_PATH, index=False)

    print(f"\n✅ Saved {len(clean)} clean rows → {CLEAN_PATH}")
    print(f"\nBy source:")
    print(clean.groupby("source").size().to_string())
    print(f"\nBy brand (top 10):")
    print(clean["brand"].value_counts().head(10).to_string())
    print(f"\nPrice stats (NPR):")
    print(f"  min:     {clean['price'].min():>10,}")
    print(f"  median:  {int(clean['price'].median()):>10,}")
    print(f"  max:     {clean['price'].max():>10,}")
    print(f"  total:   {len(clean):>10,}")


if __name__ == "__main__":
    main()