
.PHONY: up down seed migrate api web etl-cpi
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
	psql $$POSTGRES_URL -f db/seed/seed_countries.sql || true
etl-cpi:
	cd etl && python3 -m jobs.cpi --year 2024
	psql $$POSTGRES_URL -v YEAR=2024 -v CPI_CSV="$(PWD)/data/staging/cpi_2024.csv" -f scripts/load_cpi.sql
