# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Global Trust Index (GTI) project - an open data initiative that produces a credible, transparent, and updateable Global Trust Index using only programmatically accessible data sources. The project blends three pillars:

1. **Interpersonal Trust** - Survey data on whether "most people can be trusted"
2. **Institutional Trust** - Confidence in national government and institutions  
3. **Governance/Integrity Proxy** - Institutional quality measures (TI CPI, World Bank WGI)

All inputs are normalized to 0-100 scale with data provenance and confidence flags.

## Architecture

The codebase is organized into several key modules:

- **`api/`** - Fastify TypeScript API (code in `src/`)
- **`web/`** - Next.js application (routes/components in `app/`)
- **`etl/`** - Python ETL jobs (`jobs/`, `pipelines/`)
- **`db/`** - SQL migrations and seed data
- **`data/`** - Raw data, staging, and reference files
- **`scripts/`** - Development utilities

## Development Commands

### Core Development Workflow
```bash
make up      # Boot services (Postgres/Redis/MinIO), run migrations, seed demo data
make api     # Start API dev server on port 3001
make web     # Start web dev server on port 3000
make migrate # Apply db/migrations/000_init.sql to $POSTGRES_URL
make seed    # Load demo data rows
make etl-cpi # Stage CPI sample data
```

### Database Schema
The project uses Postgres with these key tables:
- `countries` - ISO3, names, regions, income groups
- `observations` - Normalized trust data (0-100 scale) per source/year/country
- `country_year` - Materialized view with computed GTI scores and confidence tiers

### Environment Setup
Copy `.env.example` to `.env` for local development. Uses Docker Compose for services:
- Postgres (port 5432)
- Redis (port 6379) 
- MinIO (ports 9000/9001)

## Data Sources & Methodology

### Approved Sources (Open/Programmatic Access Only)
- World Values Survey (WVS) - bulk CSV/SPSS
- European Social Survey (ESS) - API endpoints
- Regional Barometers (Afro/Arab/Latino/Asian) - bulk downloads
- OECD Trust Indicators - API via OECD.Stat
- Transparency International CPI - annual CSV
- World Bank WGI - API + bulk CSV

### Prohibited Sources
- Gallup World Poll (proprietary)
- Edelman Trust Barometer (restricted redistribution)

### GTI Calculation
Primary blend when all pillars available:
```
GTI = 0.4 * INSTITUTIONAL + 0.3 * INTERPERSONAL + 0.3 * GOVERNANCE
```

Governance proxy combines CPI + WGI:
```
GOV = 0.5 * CPI + 0.5 * WGI_rescaled
```

Where WGI (-2.5 to +2.5) rescales to: `((raw + 2.5) / 5) * 100`

### Confidence Tiers
- **A**: Current survey data (≤3y) + current governance proxy
- **B**: Survey >3y old OR only one pillar + governance proxy  
- **C**: Governance proxy only (no valid surveys within 7y)

## Code Style

### TypeScript/JavaScript
- 2-space indentation
- ES modules
- camelCase variables, PascalCase React components
- Use `eslint` and `tsc --noEmit` for linting/type checking

### Python
- 4-space indentation
- snake_case for modules, functions, variables
- Use `black`, `ruff`, `mypy` for formatting/linting
- Tests under `etl/tests/test_*.py` using pytest

### SQL
- Lowercase keywords
- One statement per migration when feasible

## API Contract

- `GET /api/countries` - List countries with latest GTI scores
- `GET /api/score?year=YYYY&trust_type=core` - Per-country GTI for specified year
- `GET /api/country/{iso3}?from=YYYY&to=YYYY` - Time series + pillar breakdown
- `GET /api/methodology` - Current normalization/weights (versioned JSON/YAML)

All responses include `X-GTI-Version` header and use Redis caching with `s-maxage=86400`.

## Testing

- API/UI tests: `api/src/**/*.test.ts` and under `web/`
- ETL tests: `etl/tests/test_*.py` using pytest
- Focus on GTI calculations and API contract compliance

## Data Ethics & Quality

- All displayed values must show source + year provenance
- Flag year-over-year changes >25 points for review
- Store and expose license strings for each source
- Block export if license forbids redistribution
- Never commit raw source files >10MB
- Use semantic versioning for methodology and data releases

## Security

- Never commit secrets or API keys
- Use least-privilege credentials stored in secrets manager
- Respect robots.txt and terms-of-use for all sources
- Provide data removal path for sources changing licenses