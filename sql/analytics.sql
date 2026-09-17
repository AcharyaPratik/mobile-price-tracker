cat > sql/analytics.sql <<'SQLEOF'
-- ============================================================
-- Nepal Mobile Price Tracker — Analytics Queries
-- Run in psql:
-- psql -h localhost -p 5433 -U postgres -d mobile_tracker -f sql/analytics.sql
-- ============================================================


-- ── 1. Total inventory overview ─────────────────────────────
SELECT COUNT(*)                AS total_phones,
       COUNT(DISTINCT brand)   AS distinct_brands,
       COUNT(DISTINCT source)  AS sources,
       MIN(price)              AS cheapest,
       ROUND(AVG(price))       AS avg_price,
       MAX(price)              AS most_expensive
FROM mobile_prices;


-- ── 2. Cheapest phone per brand ─────────────────────────────
SELECT DISTINCT ON (brand)
       brand, name, price, source
FROM mobile_prices
ORDER BY brand, price ASC;


-- ── 3. Average price by brand (ranked) ──────────────────────
SELECT brand,
       COUNT(*)            AS models,
       ROUND(AVG(price))   AS avg_price,
       MIN(price)          AS cheapest,
       MAX(price)          AS priciest
FROM mobile_prices
GROUP BY brand
ORDER BY avg_price DESC;


-- ── 4. Price band distribution ──────────────────────────────
SELECT price_category,
       COUNT(*) AS models,
       ROUND(MIN(price))  AS from_price,
       ROUND(MAX(price))  AS to_price
FROM mobile_prices
GROUP BY price_category
ORDER BY MIN(price);


-- ── 5. Cheapest 15 phones overall ───────────────────────────
SELECT brand, name, price, price_category, source
FROM mobile_prices
ORDER BY price ASC
LIMIT 15;


-- ── 6. Most expensive 10 phones ─────────────────────────────
SELECT brand, name, price, source
FROM mobile_prices
ORDER BY price DESC
LIMIT 10;


-- ── 7. Source coverage: how many listings each site has ────
SELECT source,
       COUNT(*) AS listings,
       ROUND(AVG(price)) AS avg_price,
       MIN(price) AS min_price,
       MAX(price) AS max_price
FROM mobile_prices
GROUP BY source
ORDER BY listings DESC;


-- ── 8. Brand price spread (min → max range) ─────────────────
SELECT brand,
       MIN(price)             AS min_price,
       MAX(price)             AS max_price,
       MAX(price) - MIN(price) AS spread
FROM mobile_prices
GROUP BY brand
HAVING COUNT(*) >= 3
ORDER BY spread DESC
LIMIT 10;


-- ── 9. Price changes (last 24h from history) ────────────────
WITH today AS (
    SELECT url, name, brand, price
    FROM price_history
    WHERE snapshot_date = CURRENT_DATE
),
yesterday AS (
    SELECT url, price
    FROM price_history
    WHERE snapshot_date = (SELECT MAX(snapshot_date)
                           FROM price_history
                           WHERE snapshot_date < CURRENT_DATE)
)
SELECT t.brand,
       t.name,
       y.price AS old_price,
       t.price AS new_price,
       t.price - y.price AS change,
       ROUND(100.0 * (t.price - y.price) / y.price, 2) AS pct
FROM today t
JOIN yesterday y ON y.url = t.url
WHERE t.price <> y.price
ORDER BY ABS(t.price - y.price) DESC
LIMIT 20;


-- ── 10. Biggest 24h drops only ──────────────────────────────
WITH today AS (
    SELECT url, name, brand, price
    FROM price_history WHERE snapshot_date = CURRENT_DATE
),
prior AS (
    SELECT url, price
    FROM price_history
    WHERE snapshot_date = (SELECT MAX(snapshot_date)
                           FROM price_history
                           WHERE snapshot_date < CURRENT_DATE)
)
SELECT t.brand, t.name,
       p.price AS old_price,
       t.price AS new_price,
       t.price - p.price AS drop
FROM today t
JOIN prior p ON p.url = t.url
WHERE t.price < p.price
ORDER BY drop ASC
LIMIT 10;
SQLEOF