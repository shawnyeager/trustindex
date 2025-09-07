# BOOTSTRAP.md — Codex Bootstrap Playbook (with UI Specs)

> Purpose: Give Codex (and humans) everything needed to spin up the Global Trust Index (GTI) from zero to an MVP — including backend, ETL, API, **and** UI wireframes.

---

## 0) Quickstart Summary

**Goal (Day 1):**
- Stand up the repo, database, and a minimal API that serves GTI (proxy) scores for 5 countries.
- Land first ETL job that ingests TI CPI into Postgres and exposes it via `/api/score?year=YYYY&trust_type=proxy`.

**One command:**
```bash
make up  # boots Postgres+Redis+MinIO, runs migrations, seeds demo data, starts API+Web
```

---

## 1) Repository Layout

```
trustindex/
├─ api/                 # Next.js API routes (default) or FastAPI if preferred
│  ├─ routes/           # /api/* endpoints
│  ├─ lib/              # db client, caching, validation
│  └─ package.json
├─ web/                 # Next.js app (UI)
│  ├─ app/              # app router
│  ├─ components/
│  └─ package.json
├─ etl/
│  ├─ jobs/             # source-specific download/parse/transform
│  │  ├─ cpi.py         # Transparency International CPI
│  │  ├─ wgi.py         # World Bank WGI
│  │  ├─ ess.py         # ESS (NSD API)
│  │  └─ wvs.py         # WVS (bulk CSV)
│  ├─ common/           # mapping utils, normalization, schema
│  ├─ pipelines/        # assemble country_year + GTI
│  └─ requirements.txt
├─ data/
│  ├─ raw/              # downloaded sources (hashed folders)
│  ├─ staging/          # standardized CSVs per source
│  └─ reference/        # iso mappings, methodology.yaml
├─ db/
│  ├─ migrations/       # sql or alembic
│  └─ seed/
├─ infra/
│  ├─ docker/
│  │  ├─ Dockerfile.api
│  │  ├─ Dockerfile.etl
│  │  └─ nginx.conf
│  └─ github/
│     └─ ci.yml
├─ scripts/
│  ├─ fetch_cpi.sh
│  ├─ refresh_tiles.sh
│  └─ dev_seed.py
├─ tiles/
│  └─ trust_core_*.mbtiles
├─ .env.example
├─ Makefile
├─ AGENTS.md            # methodology & agent duties
└─ README.md
```

---

## 2) Environment & Services

**Services:** Postgres, Redis, MinIO (for artifacts), optional vector-tiles server.

`.env.example` (copy to `.env`):
```
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trust
POSTGRES_USER=trust
POSTGRES_PASSWORD=trust

# Cache
REDIS_URL=redis://localhost:6379

# Storage (MinIO for local dev)
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=dev
S3_SECRET_KEY=devpass
S3_BUCKET=trust-artifacts

# API
NODE_ENV=development
API_PORT=3001
WEB_PORT=3000

# Feature flags
FEATURE_USE_NEXT_API=true
```

**docker-compose.yml** (excerpt):
```yaml
version: '3.9'
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports: ["5432:5432"]
    volumes: ["db_data:/var/lib/postgresql/data"]
  redis:
    image: redis:7
    ports: ["6379:6379"]
  minio:
    image: minio/minio
    command: server /data --address :9000 --console-address :9001
    environment:
      MINIO_ROOT_USER: ${S3_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${S3_SECRET_KEY}
    ports: ["9000:9000", "9001:9001"]
    volumes: ["minio_data:/data"]
volumes:
  db_data: {}
  minio_data: {}
```

---

## 3) Database Schema (DDL)

```sql
-- countries
create table if not exists countries (
  iso3 text primary key,
  iso2 text,
  name text not null,
  region text,
  income_group text
);

-- observations (normalized 0–100 scores per source-variable)
create table if not exists observations (
  id bigserial primary key,
  iso3 text references countries(iso3),
  year int not null,
  source text not null,
  trust_type text not null check (trust_type in ('interpersonal','institutional','governance','cpi','wgi','oecd','derived')),
  raw_value numeric,
  raw_unit text,
  score_0_100 numeric not null,
  sample_n int,
  method_notes text,
  source_url text,
  ingested_at timestamptz default now()
);

-- country_year (materialized view, populated by ETL)
-- columns: iso3, year, inter, inst, gov, gti, confidence_score, confidence_tier, sources_used jsonb
```

---

## 4) Methodology Contract

Create `data/reference/methodology.yaml` (drives ETL, also served by API):
```yaml
version: 0.1.0
pillars:
  interpersonal:
    weight: 0.3
    variables:
      - source: WVS
        var: TRUST_MOST_PEOPLE
        scale: percent
      - source: ESS
        var: ppl_trust_index
        scale: 0_10_to_percent
  institutional:
    weight: 0.4
    variables:
      - source: WVS
        var: trust_gov
        scale: percent
      - source: ESS
        var: trust_parliament
        scale: 0_10_to_percent
      - source: OECD
        var: trust_gov
        scale: percent
  governance:
    weight: 0.3
    components:
      - source: CPI
        var: cpi_score
        weight: 0.5
      - source: WGI
        var: avg(rule_of_law, government_effectiveness)
        weight: 0.5
scales:
  0_10_to_percent: "x * 10"
rescaling:
  wgi: "((x + 2.5) / 5) * 100"
confidence:
  survey_grace_years: 3
  decay_after_grace: 0.03
  proxy_only_tier: C
```

---

## 5) Makefile (dev ergonomics)

```makefile
.PHONY: up down seed migrate etl-cpi api web
up:
	docker compose up -d
	make migrate
	make seed
api:
	cd api && npm install && npm run dev
web:
	cd web && npm install && npm run dev
migrate:
	psql $$POSTGRES_URL -f db/migrations/000_init.sql || true
seed:
	python3 scripts/dev_seed.py
etl-cpi:
	cd etl && pip install -r requirements.txt && python -m jobs.cpi --year 2024
```

---

## 6) Minimal API Stubs

**If using Next.js API (recommended for speed):**
- `GET /api/countries` → names + iso + latest GTI (mock if empty)
- `GET /api/score?year=YYYY&trust_type=core` → join `country_year`
- `GET /api/country/{iso3}` → pillar breakdown + sources_used

Validation via Zod; caching via Redis (`Cache-Control: s-maxage=86400`).

---

## 7) ETL First Win: CPI

**Command:** `make etl-cpi`

**Flow:**
1. Download the CPI CSV to `data/raw/cpi/{year}/cpi.csv`.
2. Parse country → ISO3 (use `data/reference/iso_map.csv`).
3. Normalize (CPI already 0–100). Write standardized rows to `data/staging/cpi_{year}.csv`.
4. Upsert into `observations` with `trust_type='cpi'` and `governance` rows if computing GOV here.
5. Trigger Assemble pipeline to compute `country_year` (GOV only until surveys arrive).

**CLI:**
```bash
python -m pipelines.assemble --year 2024 --sources CPI WGI
```

---

## 8) UI Wireframes (ASCII Mockups)

> These guide Codex to scaffold components and routes. See AGENTS.md for conceptual model.

### Main Map Screen
```
Header
└─ [Logo/“Trust Index”]   [Search country/region]   [Year slider ◀─●─▶]   [Download]

Main
├─ Left Panel (Filters)
│  ├─ MODE
│  │   • Core Trust Score (GTI)
│  │   • Interpersonal
│  │   • Institutional
│  ├─ OVERLAYS
│  │   ☐ Regional barometers  ☐ CPI  ☐ WGI  ☐ OECD  ☐ Pew
│  ├─ COLOR SCALE
│  │   • Quantiles  • Continuous  • Diverging
│  └─ DATA NOTES (source + vintage)
│
├─ Map (choropleth)
│  └─ Hover tooltip: Country • Score (0–100) • Source/year • mini trend
│
└─ Right Panel (Details)
   ├─ Country header: Flag • Name • Compare button
   ├─ KPI cards: Core / Interpersonal / Institutional
   ├─ Time series chart (10–20y)
   ├─ Source breakdown table (value, year, sample)
   └─ Comparisons: region avg • income peers
```

### Components to Scaffold
- `MapView` (Mapbox GL / MapLibre) — reads vector tiles
- `YearSlider` — snaps to available years
- `FilterPanel` — mode/overlay toggles; writes to global state (Zustand)
- `CountryPanel` — fetches `/api/country/{iso3}`; renders KPIs + D3 chart
- `CompareDrawer` — select peers; multi-line chart

---

## 9) Seed Data & Reference Files

**`data/reference/iso_map.csv` (excerpt):**
```
iso3,iso2,name
SWE,SE,Sweden
USA,US,United States
BRA,BR,Brazil
NGA,NG,Nigeria
IND,IN,India
```

**`db/seed/seed_countries.sql`:** insert the above.

**`scripts/dev_seed.py`** should:
- insert countries
- create 5 mock `observations` rows per country (inter, inst, gov) for the latest year

---

## 10) CI/CD (GitHub Actions)

`.github/workflows/ci.yml` (key steps):
- Setup Node + Python
- Lint (`eslint`, `black`, `ruff`) and type-check (`tsc`, `mypy`)
- Spin up Postgres service; run migrations; run unit tests
- Build web+api
- On `main`: push Docker images; deploy via your target (e.g., Fly.io/Vercel)

---

## 11) Codex Agent Playbooks

> Paste these prompts into your orchestration of Codex agents.

**Agent: Repo Scaffolder**
- “Create the directory tree from Section 1; generate placeholder files with headers and TODOs; add `.gitignore` for Node, Python, and data folders; initialize npm workspaces in `/web` and `/api`; initialize Python venv in `/etl`.”

**Agent: DB & Migrations**
- “Generate SQL migration file `db/migrations/000_init.sql` with the tables in Section 3; add a script to apply migrations using `psql`; wire `make migrate`.”

**Agent: CPI ETL**
- “Implement `etl/jobs/cpi.py` to download CPI CSV for a given year, map ISO3, normalize to 0–100, and load into `observations`. Create `pipelines/assemble.py` that constructs `country_year` rows computing GOV from CPI (and WGI if present).”

**Agent: API Stubs**
- “Implement Next.js API routes for `/api/countries`, `/api/score`, `/api/country/[iso3]` using `pg` client; add Redis caching; return shapes defined in AGENTS.md.”

**Agent: Web Skeleton**
- “Build a minimal Next.js `/` page using the wireframes in Section 8; add `MapView`, `FilterPanel`, `YearSlider`, `CountryPanel` components calling the API.”

**Agent: CI Setup**
- “Create GitHub Actions workflow per Section 10; add lint configs; ensure PR checks run migrations and unit tests.”

**Agent: QA Hooks**
- “Implement outlier check util in `etl/common/qa.py` (Δ>25 points y/y flag) and integrate into assemble pipeline with a console summary.”

---

## 12) MVP Definition of Done

- [ ] `make up` runs without errors; services respond.
- [ ] `/api/score?year=YYYY&trust_type=proxy` returns CPI-based GOV scores for 5+ seed countries.
- [ ] Web map renders with country colors from API; tooltip + right panel show mock breakdown.
- [ ] Methodology served at `/api/methodology` (from YAML).
- [ ] Release notes template generated on first run in `releases/`.

---

## 13) Next Steps After MVP

- Add **WGI ETL** and merge into GOV (50/50 with CPI).
- Add **ESS API ingestion** for select countries; compute INST/INTER.
- Add **time slider** and **confidence tiers**.
- Swap placeholder tiles with real vector tiles (tippecanoe → mbtiles → tileserver-gl/MapLibre tiles).

---

## 14) Conventions

- **TypeScript:** strict mode ON.
- **Python:** `black`, `ruff`, `mypy`.
- **Commits:** Conventional Commits.
- **Data:** Never commit raw source files >10MB; store hashes and fetch scripts instead.

---

**This playbook is intentionally prescriptive so Codex can execute it step-by-step without additional guidance.**

