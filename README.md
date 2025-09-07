# trustindex starter

This is a minimal scaffold with API, ETL, DB schema, and a tiny web placeholder.

## Docs & Guides
- Methodology and agent spec: [AGENTS.md](AGENTS.md)
- Contributor guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Bootstrap playbook and UI specs: [BOOTSTRAP.md](BOOTSTRAP.md)

## Quickstart
- Copy `.env.example` to `.env` and adjust as needed.
- Start services, run migrations, and seed demo data: `make up`
- Run API dev server: `make api` (defaults to `http://localhost:3001`)
- Run Web dev server: `make web` (defaults to `http://localhost:3000`)

Endpoints to try:
- `GET http://localhost:3001/api/countries`
- `GET http://localhost:3001/api/score?year=2024&trust_type=core`
