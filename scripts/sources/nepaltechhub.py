"""
NepalTechHub extractor.

Source: https://www.nepaltechhub.com/phones/
Method: requests + BeautifulSoup (server-rendered, paginated via /page/N/)
"""

import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.nepaltechhub.com/phones/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
DELAY_SECONDS = 1.5


def fetch(url: str) -> str | None:
    """Download a page. Returns HTML or None on failure."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        print(f"  ⚠️  {url}: {e}")
        return None


def parse(html: str) -> list[dict]:
    """Extract phone cards from a listing page."""
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict] = []
    now = datetime.now().isoformat(timespec="seconds")

    for card in soup.select("article.nth-neo-card--phones"):
        name_el   = card.select_one(".nth-neo-title a")
        brand_el  = card.select_one(".nth-neo-brand")
        price_el  = card.select_one(".nth-neo-best")
        status_el = card.select_one(".nth-neo-status-text")

        if not name_el:
            continue

        url = name_el.get("href", "")
        slug = url.rstrip("/").rsplit("/", 1)[-1] if url else ""

        rows.append({
            "source":     "nepaltechhub",
            "source_id":  slug,
            "name":       name_el.get_text(strip=True),
            "brand":      brand_el.get_text(strip=True) if brand_el else "",
            "price_raw":  price_el.get_text(strip=True) if price_el else "",
            "price_npr":  "",                        # cleaned in transform.py
            "status":     status_el.get_text(strip=True) if status_el else "",
            "url":        url,
            "scraped_at": now,
        })
    return rows


def scrape(max_pages: int | None = None) -> list[dict]:
    """Scrape every page. max_pages=None means 'all'."""
    all_rows: list[dict] = []

    first = fetch(BASE_URL)
    if not first:
        print("  nepaltechhub: could not fetch landing page")
        return []

    m = re.search(r"Page\s+\d+\s+of\s+(\d+)", first)
    detected = int(m.group(1)) if m else 1
    total = detected if max_pages is None else min(detected, max_pages)

    page_rows = parse(first)
    all_rows.extend(page_rows)
    print(f"  nepaltechhub: page 1/{total} → +{len(page_rows)} ({len(all_rows)} total)")

    for p in range(2, total + 1):
        time.sleep(DELAY_SECONDS)
        html = fetch(f"{BASE_URL}page/{p}/")
        if not html:
            continue
        page_rows = parse(html)
        all_rows.extend(page_rows)
        print(f"  nepaltechhub: page {p}/{total} → +{len(page_rows)} ({len(all_rows)} total)")

    return all_rows