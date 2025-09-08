-- Global Trust Index Database Schema
-- Migration 000: Initial tables

-- Enable PostGIS extension (optional for future geospatial features)
-- CREATE EXTENSION IF NOT EXISTS postgis;

-- Countries reference table
CREATE TABLE IF NOT EXISTS countries (
    iso3 TEXT PRIMARY KEY,
    iso2 TEXT,
    name TEXT NOT NULL,
    region TEXT,
    income_group TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Raw observations from all sources
CREATE TABLE IF NOT EXISTS observations (
    id BIGSERIAL PRIMARY KEY,
    iso3 TEXT REFERENCES countries(iso3),
    year INTEGER NOT NULL,
    source TEXT NOT NULL,
    trust_type TEXT NOT NULL CHECK (trust_type IN (
        'interpersonal', 'institutional', 'governance', 
        'cpi', 'wgi', 'oecd', 'derived'
    )),
    raw_value NUMERIC,
    raw_unit TEXT,
    score_0_100 NUMERIC NOT NULL CHECK (score_0_100 >= 0 AND score_0_100 <= 100),
    sample_n INTEGER,
    method_notes TEXT,
    source_url TEXT,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique observations per country-year-source-trust_type
    UNIQUE(iso3, year, source, trust_type)
);

-- Materialized view for country-year aggregated scores
CREATE TABLE IF NOT EXISTS country_year (
    iso3 TEXT REFERENCES countries(iso3),
    year INTEGER NOT NULL,
    interpersonal NUMERIC CHECK (interpersonal >= 0 AND interpersonal <= 100),
    institutional NUMERIC CHECK (institutional >= 0 AND institutional <= 100),
    governance NUMERIC CHECK (governance >= 0 AND governance <= 100),
    gti NUMERIC CHECK (gti >= 0 AND gti <= 100),
    confidence_score NUMERIC CHECK (confidence_score >= 0 AND confidence_score <= 1),
    confidence_tier CHAR(1) CHECK (confidence_tier IN ('A', 'B', 'C')),
    sources_used JSONB,
    version TEXT DEFAULT '0.1.0',
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (iso3, year)
);

-- Source metadata table
CREATE TABLE IF NOT EXISTS source_metadata (
    source TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    cadence TEXT,
    coverage TEXT,
    license TEXT,
    access_mode TEXT,
    weighting_notes TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_observations_country_year ON observations(iso3, year);
CREATE INDEX IF NOT EXISTS idx_observations_trust_type_year ON observations(trust_type, year);
CREATE INDEX IF NOT EXISTS idx_country_year_year ON country_year(year);
CREATE INDEX IF NOT EXISTS idx_country_year_gti ON country_year(gti DESC);

-- GIN index for JSONB sources_used
CREATE INDEX IF NOT EXISTS idx_country_year_sources_gin ON country_year USING GIN(sources_used);

-- Insert initial source metadata
INSERT INTO source_metadata (source, description, cadence, coverage, license, access_mode) VALUES
    ('CPI', 'Transparency International Corruption Perceptions Index', 'Annual', 'Global', 'CC BY-ND 4.0', 'CSV Download'),
    ('WGI', 'World Bank Worldwide Governance Indicators', 'Annual', 'Global', 'CC BY 4.0', 'API + CSV'),
    ('WVS', 'World Values Survey', 'Wave (~5 years)', 'Global (uneven)', 'Custom Terms', 'Bulk Download'),
    ('ESS', 'European Social Survey', 'Biennial', 'Europe', 'CC BY-NC 4.0', 'API + Download'),
    ('OECD', 'OECD Trust Indicators', 'Irregular', 'OECD Countries', 'OECD Terms', 'OECD.Stat API')
ON CONFLICT (source) DO NOTHING;