-- Reference schema for the Price Monitor project.
-- NOTE: in normal use, the backend creates these tables automatically on
-- startup via SQLAlchemy (see backend/app/database.py -> init_db()).
-- This file is provided for manual inspection / manual DB setup (e.g. if
-- you want to create the schema yourself on Supabase before first boot).

CREATE TYPE product_category AS ENUM ('new', 'stock', 'unknown');

CREATE TABLE IF NOT EXISTS products (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(500) NOT NULL,
    warehouse_title  VARCHAR(200),
    url              TEXT,
    digikala_url     TEXT,
    torob_url        TEXT,
    category         product_category NOT NULL DEFAULT 'unknown',
    quantity         INTEGER,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_products_name ON products (name);

CREATE TABLE IF NOT EXISTS stores (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(255) NOT NULL UNIQUE,
    kind  VARCHAR(50) NOT NULL DEFAULT 'torob_seller'  -- 'digikala' | 'torob_seller'
);

CREATE TABLE IF NOT EXISTS prices (
    id           SERIAL PRIMARY KEY,
    product_id   INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    store_id     INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    price        BIGINT,                 -- تومان؛ NULL = ناموجود
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    url          TEXT,
    checked_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (product_id, store_id)
);
CREATE INDEX IF NOT EXISTS ix_prices_product_checked ON prices (product_id, checked_at);

CREATE TABLE IF NOT EXISTS price_history (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    store_id        INTEGER REFERENCES stores(id) ON DELETE SET NULL,
    old_price       BIGINT,
    new_price       BIGINT,
    change_percent  DOUBLE PRECISION,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_history_product_created ON price_history (product_id, created_at);
