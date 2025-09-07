
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
	python3 scripts/dev_seed.py
etl-cpi:
	cd etl && python3 -m jobs.cpi --year 2024
