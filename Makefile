.PHONY: up down migrate seed api web etl-cpi clean logs

# Load environment variables
include .env
export

up:
	docker compose up -d --wait
	@echo "Waiting for services to be ready..."
	@sleep 5
	$(MAKE) migrate
	$(MAKE) seed

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v
	docker system prune -f

migrate:
	@echo "Running database migrations..."
	@if [ -f db/migrations/000_init.sql ]; then \
		PGPASSWORD=$(POSTGRES_PASSWORD) psql -h $(POSTGRES_HOST) -p $(POSTGRES_PORT) -U $(POSTGRES_USER) -d $(POSTGRES_DB) -f db/migrations/000_init.sql; \
	else \
		echo "Migration file not found"; \
	fi

seed:
	@echo "Seeding database..."
	@cd scripts && python3 dev_seed.py

api:
	@echo "Starting API server..."
	@cd api && npm install && npm run dev

web:
	@echo "Starting web server..."
	@cd web && npm install && npm run dev

etl-cpi:
	@echo "Running CPI ETL job..."
	@cd etl && pip install -r requirements.txt && python jobs/cpi.py --year 2024
	@cd etl && python pipelines/assemble.py --year 2024 --sources CPI

install:
	@echo "Installing dependencies..."
	@cd api && npm install
	@cd web && npm install
	@cd etl && pip install -r requirements.txt

test:
	@echo "Running tests..."
	@cd api && npm run test
	@cd etl && pytest

lint:
	@echo "Running linters..."
	@cd api && npm run lint && npm run typecheck
	@cd web && npm run lint && npm run typecheck
	@cd etl && black . && ruff . && mypy .