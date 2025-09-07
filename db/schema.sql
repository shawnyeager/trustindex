-- Postgres schema for Global Trust Index (init stub)

CREATE TABLE IF NOT EXISTS countries (
  iso3 TEXT PRIMARY KEY,
  iso2 TEXT,
  name TEXT NOT NULL,
  region TEXT,
  income_group TEXT
);

CREATE TABLE IF NOT EXISTS observations (
  id BIGSERIAL PRIMARY KEY,
  iso3 TEXT NOT NULL,
  year INT NOT NULL,
  source TEXT NOT NULL,
  trust_type TEXT NOT NULL CHECK (trust_type IN ('interpersonal','institutional','governance','wgi','cpi','oecd','derived')),
  raw_value DOUBLE PRECISION,
  raw_unit TEXT,
  score_0_100 DOUBLE PRECISION,
  sample_n INT,
  method_notes TEXT,
  source_url TEXT,
  ingested_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_observations_iso3_year ON observations(iso3, year);
CREATE INDEX IF NOT EXISTS idx_observations_trust_year ON observations(trust_type, year);

-- Placeholder for materialized view; define when DB is connected
-- CREATE MATERIALIZED VIEW country_year AS
-- SELECT ...;

CREATE TABLE IF NOT EXISTS source_metadata (
  source TEXT PRIMARY KEY,
  description TEXT,
  cadence TEXT,
  coverage TEXT,
  license TEXT,
  access_mode TEXT,
  weighting_notes TEXT
);

