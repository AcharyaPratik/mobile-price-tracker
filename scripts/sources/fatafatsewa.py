import time
from datetime import datetime

from playwright.sync_api import sync_playwright

BASE_URL = "https://fatafatsewa.com/category/mobile-price-in-nepal"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def extract_card(card) -> dict | None:
    name_el  = card.query_selector("h3")
    brand_el = card.query_selector('p[class*="uppercase"][class*="tracking-widest"]')
    price_el = card.query_selector('p[class*="font-bold"][class*="tracking-tight"]')

    if not (name_el and price_el):
        return None

    price_text = price_el.inner_text().replace("\n", " ").strip()
    digits = "".join(ch for ch in price_text if ch.isdigit())
    href = card.get_attribute("href") or ""

    return {
        "source":     "fatafatsewa",
        "source_id":  href.rstrip("/").rsplit("/", 1)[-1],
        "name":       name_el.inner_text().strip(),
        "brand":      brand_el.inner_text().strip() if brand_el else "",
        "price_raw":  price_text,
        "price_npr":  digits,
        "status":     "InStock",
        "url":        "https://fatafatsewa.com" + href,
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
    }


def get_product_hrefs(page) -> list[str]:
    """Return the current set of product hrefs, in order."""
    return [
        c.get_attribute("href") or ""
        for c in page.query_selector_all('a[href^="/product-detail/"]')
    ]


def wait_for_page_change(page, old_hrefs: list[str], timeout_s: int = 20) -> bool:
    """Poll until the product list changes (or timeout)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(0.5)
        new_hrefs = get_product_hrefs(page)
        if new_hrefs and new_hrefs != old_hrefs:
            # also make sure the DOM isn't just reshuffled — first item should differ
            if new_hrefs[0] != old_hrefs[0] if old_hrefs else True:
                return True
    return False


def scrape(max_pages: int | None = None) -> list[dict]:
    all_rows: list[dict] = []
    seen_urls: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=USER_AGENT)
        page = ctx.new_page()

        try:
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"  fatafatsewa: could not load page: {e}")
            browser.close()
            return []

        page_num = 1
        while True:
            if max_pages is not None and page_num > max_pages:
                break

            time.sleep(1.0)
            cards = page.query_selector_all('a[href^="/product-detail/"]')

            new_rows: list[dict] = []
            for c in cards:
                row = extract_card(c)
                if row and row["url"] not in seen_urls:
                    seen_urls.add(row["url"])
                    new_rows.append(row)

            if not new_rows:
                print(f"  fatafatsewa: page {page_num} → nothing new, stopping")
                break

            all_rows.extend(new_rows)
            print(f"  fatafatsewa: page {page_num} → +{len(new_rows)} ({len(all_rows)} total)")

            if max_pages is not None and page_num >= max_pages:
                break

            # capture the current set of product hrefs
            old_hrefs = get_product_hrefs(page)

            # scroll to the bottom so the pagination control is in view
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(0.5)

            # click "Next" via JS — bypasses sticky-header interception
            clicked = page.evaluate("""() => {
                const next = document.querySelector('a[aria-label="Go to next page"]');
                if (!next) return false;
                next.scrollIntoView({block: 'center'});
                next.click();
                return true;
            }""")

            if not clicked:
                print("  fatafatsewa: no 'Next' button, done")
                break

            # wait for the grid to actually change
            if not wait_for_page_change(page, old_hrefs, timeout_s=20):
                print(f"  fatafatsewa: page {page_num + 1} did not load, stopping")
                break

            # let the new page settle before scraping
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            time.sleep(1.0)

            page_num += 1

        browser.close()
    return all_rows