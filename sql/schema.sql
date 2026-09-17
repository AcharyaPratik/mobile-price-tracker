\c mobile_tracker

DROP TABLE IF EXISTS mobile_prices CASCADE;

CREATE TABLE mobile_prices (
    id              SERIAL PRIMARY KEY,
    source          VARCHAR(50)    NOT NULL,
    name            VARCHAR(255)   NOT NULL,
    brand           VARCHAR(100)   NOT NULL,
    price           NUMERIC(10, 0) NOT NULL,
    price_category  VARCHAR(20),
    url             TEXT           NOT NULL,
    scraped_at      TIMESTAMP      NOT NULL,
    created_at      TIMESTAMP      DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_mobile_prices_source_url
    ON mobile_prices (source, url);

CREATE INDEX idx_mobile_prices_brand   ON mobile_prices (brand);
CREATE INDEX idx_mobile_prices_price   ON mobile_prices (price);

-- ── historical snapshots ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS price_history (
    id              BIGSERIAL PRIMARY KEY,
    source          VARCHAR(50)    NOT NULL,
    url             TEXT           NOT NULL,
    name            VARCHAR(255)   NOT NULL,
    brand           VARCHAR(100)   NOT NULL,
    price           NUMERIC(10, 0) NOT NULL,
    snapshot_date   DATE           NOT NULL,
    captured_at     TIMESTAMP      NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_history_url_date ON price_history (url, snapshot_date);
CREATE INDEX idx_history_brand    ON price_history (brand);
