# Repository Guidelines

This guide helps contributors work effectively in this repo while staying aligned with the Global Trust Index (GTI) methodology and open‑data constraints.

## Project Structure & Module Organization
- `api/` Fastify TypeScript API (code in `src/`).
- `web/` Next.js app (routes/components in `app/`).
- `etl/` Python ETL jobs (`jobs/`, `pipelines/`).
- `db/` SQL migrations and seeds; `data/` raw/staging/reference.
- `scripts/` dev utilities; `Makefile` common tasks.

## Build, Test, and Development Commands
- `make up` boots services, runs migrations, seeds demo data.
- `make api` starts API dev server on `:3001`.
- `make web` starts web dev server on `:3000`.
- `make migrate` applies `db/migrations/000_init.sql` to `$POSTGRES_URL`.
- `make seed` loads demo rows; `make etl-cpi` stages CPI sample data.

## Coding Style & Naming Conventions
- TypeScript/JS: 2‑space indent, ES modules; `camelCase` vars, `PascalCase` React components.
- Python: 4‑space indent; `snake_case` modules, functions, and variables.
- SQL: lowercase keywords; one statement per migration when feasible.
- Recommended tools: TS `eslint` + `tsc --noEmit`; Python `black`, `ruff`, `mypy`.

## Testing Guidelines
- API/UI: place tests under `api/src/**/*.test.ts` and in `web/` as added.
- ETL: use Pytest under `etl/tests/test_*.py` for normalization/assembly.
- Cover GTI calculations and API contracts (see `AGENTS.md` for shapes).

## Commit & Pull Request Guidelines
- Commits: Conventional Commits (e.g., `feat(api): add /api/methodology`).
- PRs: clear description, linked issues, screenshots for UI, sample requests/responses for APIs, and notes on data/licensing impact.
- Keep changes scoped; update docs when touching methodology or API.

## Security & Configuration Tips
- Copy `.env.example` → `.env`; never commit secrets or large data files.
- Use `$POSTGRES_URL` and services in `docker-compose.yml` for local dev.
- Only use open/programmatically accessible sources; avoid proprietary data.

