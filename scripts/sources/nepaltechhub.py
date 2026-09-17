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


def fetch(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse(html):
    soup = BeautifulSoup(html, "lxml")
    rows = []

    for card in soup.select("article.nth-neo-card--phones"):
        name_el = card.select_one(".nth-neo-title a")

        if not name_el:
            continue

        brand_el = card.select_one(".nth-neo-brand")
        price_el = card.select_one(".nth-neo-best")
        status_el = card.select_one(".nth-neo-status-text")

        url = name_el.get("href", "")

        rows.append({
            "source": "nepaltechhub",
            "source_id": url.rstrip("/").rsplit("/", 1)[-1],
            "name": name_el.get_text(strip=True),
            "brand": brand_el.get_text(strip=True) if brand_el else "",
            "price_raw": price_el.get_text(strip=True) if price_el else "",
            "price_npr": "",
            "status": status_el.get_text(strip=True) if status_el else "",
            "url": url,
            "scraped_at": datetime.now().isoformat(timespec="seconds"),
        })

    return rows


def scrape(max_pages=None):
    first_page = fetch(BASE_URL)

    if not first_page:
        return []

    match = re.search(r"Page\s+\d+\s+of\s+(\d+)", first_page)

    total_pages = int(match.group(1)) if match else 1

    if max_pages:
        total_pages = min(total_pages, max_pages)

    rows = parse(first_page)

    print(f"Page 1/{total_pages} → {len(rows)} rows")

    for page in range(2, total_pages + 1):
        time.sleep(DELAY_SECONDS)

        html = fetch(f"{BASE_URL}page/{page}/")

        if not html:
            continue

        page_rows = parse(html)

        rows.extend(page_rows)

        print(
            f"Page {page}/{total_pages} → "
            f"+{len(page_rows)} ({len(rows)} total)"
        )

    return rows