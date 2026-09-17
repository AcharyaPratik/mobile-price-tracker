import time
from datetime import datetime

from playwright.sync_api import sync_playwright

BASE_URL = "https://fatafatsewa.com/category/mobile-price-in-nepal"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def extract_card(card):
    name_el = card.query_selector("h3")
    brand_el = card.query_selector(
        'p[class*="uppercase"][class*="tracking-widest"]'
    )
    price_el = card.query_selector(
        'p[class*="font-bold"][class*="tracking-tight"]'
    )

    if not (name_el and price_el):
        return None

    href = card.get_attribute("href") or ""
    price_text = price_el.inner_text().replace("\n", " ").strip()

    return {
        "source": "fatafatsewa",
        "source_id": href.rstrip("/").rsplit("/", 1)[-1],
        "name": name_el.inner_text().strip(),
        "brand": brand_el.inner_text().strip() if brand_el else "",
        "price_raw": price_text,
        "price_npr": "".join(ch for ch in price_text if ch.isdigit()),
        "status": "InStock",
        "url": f"https://fatafatsewa.com{href}",
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
    }


def get_product_hrefs(page):
    return [
        card.get_attribute("href") or ""
        for card in page.query_selector_all(
            'a[href^="/product-detail/"]'
        )
    ]


def wait_for_page_change(page, old_hrefs, timeout=20):
    end_time = time.time() + timeout

    while time.time() < end_time:
        time.sleep(0.5)

        new_hrefs = get_product_hrefs(page)

        if (
            new_hrefs
            and new_hrefs != old_hrefs
            and (
                not old_hrefs
                or new_hrefs[0] != old_hrefs[0]
            )
        ):
            return True

    return False


def scrape(max_pages=None):
    all_rows = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=USER_AGENT
        )

        page = context.new_page()

        try:
            page.goto(
                BASE_URL,
                wait_until="networkidle",
                timeout=30000,
            )
        except Exception as e:
            print(f"Failed to load page: {e}")
            browser.close()
            return []

        page_number = 1

        while True:

            if max_pages and page_number > max_pages:
                break

            time.sleep(1)

            cards = page.query_selector_all(
                'a[href^="/product-detail/"]'
            )

            page_rows = []

            for card in cards:
                row = extract_card(card)

                if row and row["url"] not in seen_urls:
                    seen_urls.add(row["url"])
                    page_rows.append(row)

            if not page_rows:
                print(
                    f"Page {page_number}: "
                    "no new products found"
                )
                break

            all_rows.extend(page_rows)

            print(
                f"Page {page_number} → "
                f"+{len(page_rows)} "
                f"({len(all_rows)} total)"
            )

            if max_pages and page_number >= max_pages:
                break

            current_hrefs = get_product_hrefs(page)

            page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)"
            )

            time.sleep(0.5)

            clicked = page.evaluate("""
                () => {
                    const next = document.querySelector(
                        'a[aria-label="Go to next page"]'
                    );

                    if (!next) return false;

                    next.scrollIntoView({ block: "center" });
                    next.click();

                    return true;
                }
            """)

            if not clicked:
                print("No next button found")
                break

            changed = wait_for_page_change(
                page,
                current_hrefs
            )

            if not changed:
                print(
                    f"Page {page_number + 1} "
                    "did not load"
                )
                break

            try:
                page.wait_for_load_state(
                    "networkidle",
                    timeout=5000
                )
            except Exception:
                pass

            time.sleep(1)

            page_number += 1

        browser.close()

    return all_rows