.PHONY: up down seed migrate etl-cpi api web fmt lint db demo-data compute-governance-sql

up:
	docker compose up -d
	$(MAKE) migrate
	$(MAKE) seed

down:
	docker compose down

migrate:
	psql $$POSTGRES_URL -f db/migrations/000_init.sql || true

seed:
	python3 scripts/dev_seed.py

etl-cpi:
	cd etl && pip install -r requirements.txt && python -m jobs.cpi --year 2024 --input ../data/reference/example_cpi.csv --out ../data/staging

load-cpi:
	cd etl && pip install -r requirements.txt && python -m jobs.load_cpi_to_db --year 2024 --csv ../data/staging/cpi_2024.csv

etl-wgi:
	cd etl && pip install -r requirements.txt && python -m jobs.wgi --year 2024 --input ../data/reference/example_wgi.csv --out ../data/staging

load-wgi:
	cd etl && pip install -r requirements.txt && python -m jobs.load_wgi_to_db --year 2024 --csv ../data/staging/wgi_2024.csv

compute-governance:
	cd etl && pip install -r requirements.txt && python -m pipelines.compute_governance_to_db --year 2024

api:
	uvicorn api.main:app --reload

run-api: api

fmt:
	@echo "(formatter not configured in init)"

lint:
	@echo "(linter not configured in init)"

db:
	@echo "Use 'make migrate' to apply db/migrations/000_init.sql"

web:
	@echo "Web (Next.js) not scaffolded in this FastAPI-first init."

smoke:
	python3 scripts/smoke_test.py

.PHONY: fetch-world
fetch-world:
	python3 scripts/fetch_world_geojson.py

# Load example CPI/WGI CSVs and compute governance using SQL inside Postgres
demo-data:
	# CPI staging and upsert
	docker compose exec -T db psql -U trust -d trust -c "drop table if exists staging_cpi; create table staging_cpi (iso3 text, year int, cpi numeric)"
	sed '/^$$/d' data/reference/example_cpi.csv | docker compose exec -T db psql -U trust -d trust -c "COPY staging_cpi (iso3,year,cpi) FROM STDIN WITH CSV HEADER"
	docker compose exec -T db psql -U trust -d trust -c "delete from observations where trust_type = 'cpi' and year=2024; insert into observations (iso3,year,source,trust_type,score_0_100,source_url) select upper(iso3), year, 'CPI','cpi', cpi::numeric, 'https://www.transparency.org/en/cpi' from staging_cpi; drop table staging_cpi"
	# WGI staging and upsert (rescaled to 0–100 per AGENTS.md)
	docker compose exec -T db psql -U trust -d trust -c "drop table if exists staging_wgi; create table staging_wgi (iso3 text, year int, rule_of_law numeric, government_effectiveness numeric)"
	sed '/^$$/d' data/reference/example_wgi.csv | docker compose exec -T db psql -U trust -d trust -c "COPY staging_wgi (iso3,year,rule_of_law,government_effectiveness) FROM STDIN WITH CSV HEADER"
	docker compose exec -T db psql -U trust -d trust -c "delete from observations where trust_type='wgi' and year=2024; insert into observations (iso3,year,source,trust_type,score_0_100,source_url) select upper(iso3), year, 'WGI','wgi', ROUND(((( (rule_of_law::numeric + government_effectiveness::numeric) / 2.0 ) + 2.5) / 5.0) * 100.0, 2), 'https://info.worldbank.org/governance/wgi/' from staging_wgi; drop table staging_wgi"
	# Compute derived governance rows for 2024
	$(MAKE) compute-governance-sql

# Compute and store GOV = 0.5*CPI + 0.5*WGI (or passthrough) into observations via SQL
compute-governance-sql:
	docker compose exec -T db psql -U trust -d trust -c "delete from observations where trust_type='governance' and year=2024"
	docker compose exec -T db psql -U trust -d trust -c "\
with cpi as (select iso3, score_0_100 as cpi from observations where year=2024 and trust_type='cpi'),\
     wgi as (select iso3, score_0_100 as wgi from observations where year=2024 and trust_type='wgi'),\
     joined as (\
       select coalesce(cpi.iso3, wgi.iso3) as iso3, cpi.cpi, wgi.wgi,\
              case when cpi.cpi is not null and wgi.wgi is not null then 0.5*cpi.cpi + 0.5*wgi.wgi\
                   else coalesce(cpi.cpi, wgi.wgi) end as gov\
         from cpi full outer join wgi on wgi.iso3 = cpi.iso3\
     )\
insert into observations (iso3, year, source, trust_type, raw_value, raw_unit, score_0_100, sample_n, method_notes, source_url)\
select iso3, 2024, 'GOV', 'governance', NULL, NULL, gov, NULL,\
       'Derived: GOV = 0.5*CPI + 0.5*WGI when both present; else passthrough',\
       'https://www.transparency.org/en/cpi;https://info.worldbank.org/governance/wgi/'\
  from joined where gov is not null;"
