# Global Trust Index (Open Data) [![CI](https://github.com/shawnyeager/trustindex/actions/workflows/ci.yml/badge.svg)](https://github.com/shawnyeager/trustindex/actions/workflows/ci.yml)

Minimal scaffold for the Global Trust Index (GTI): API stubs, ETL structure, and DB schema aligned with AGENTS.md.

## Quickstart

- One command (services + seed): `cp .env.example .env && make up`
  - Starts Postgres, Redis, MinIO via Docker Compose
  - Starts FastAPI container (`api`) on port 8000
  - Applies initial migration and seeds mock governance data
  - You can also run the API locally with Uvicorn if preferred

- Load demo CPI/WGI data (optional but recommended for API responses):
  - `make demo-data` → loads example CPI and WGI CSVs into Postgres and computes governance rows for 2024.
  - Optional offline basemap: `make fetch-world` → downloads Natural Earth 110m GeoJSON to `data/reference/world-110m.geojson`; rebuild API (`docker compose build api && docker compose up -d api`).

- API (FastAPI dev):
  - `python -m venv .venv && source .venv/bin/activate && pip install -r api/requirements.txt`
  - Ensure `POSTGRES_URL` is set (copy `.env.example` to `.env`)
  - `uvicorn api.main:app --reload` → browse `http://localhost:8000/docs`
  - Endpoints now read from Postgres; if not available, they return seeded/mock fallback data

- DB schema:
  - `make migrate` applies `db/migrations/000_init.sql` to `$POSTGRES_URL`.

- ETL:
  - CPI pipeline stub: `python -m etl.jobs.cpi --year 2024 --input data/reference/example_cpi.csv --out data/staging`
  - WGI pipeline stub: `python -m etl.jobs.wgi --year 2024 --input data/reference/example_wgi.csv --out data/staging`
  - Assemble GOV-only `country_year`: `python -m etl.pipelines.assemble --year 2024 --cpi data/staging/cpi_2024.csv --out data/staging/country_year.csv`
- Load CPI into Postgres: `make load-cpi` (uses `POSTGRES_URL`)
- Load WGI into Postgres: `make load-wgi`
- Compute and store GOV (50/50 CPI+WGI if both present): `make compute-governance`

## Smoke Test
- With the API running (via `make up` or `make api`), run: `make smoke`
- Verifies:
  - `/api/score?year=2024&trust_type=proxy` returns at least 5 countries (USA,SWE,BRA,NGA,IND)
  - `/api/countries` returns data
  - `/api/country/USA?from=2024&to=2024` returns a 1-item series

Tip: For a clean start: `make down && make up && make demo-data && make smoke`.

To enable offline map polygons: `make fetch-world && docker compose build api && docker compose up -d api`.

**CI Expectations**
- Runs `docker compose up -d` to start `db`, `redis`, `minio`, and `api`.
- Applies `db/migrations/000_init.sql` and seeds countries.
- Normalizes and loads example CPI/WGI, computes governance.
- Waits for API on `http://localhost:8000` and runs `scripts/smoke_test.py`.
- Fails the check if any step or smoke assertion fails.

## Layout

- `api/` FastAPI app exposing endpoints from AGENTS.md
- `etl/` ETL building blocks + jobs/pipelines (CPI first win)
- `db/` migrations and seed files
- `data/` reference (methodology, iso map) + staging
- `infra/` docker compose (root) for local services
- `AGENTS.md` methodology and agent workflows

## API behavior (proxy/GOV)
- `/api/score?year=YYYY&trust_type=proxy` computes governance on the fly as 0.5*CPI + 0.5*WGI when both exist for that year; otherwise uses the available one.
- `/api/countries` uses the latest year where CPI or WGI exists per country and reports that computed governance value as the latest GTI.

## Next Steps

- Wire API to Postgres for real data
- Implement source-specific ingestors and mappers
- Add confidence scoring and materialized view for `country_year`
