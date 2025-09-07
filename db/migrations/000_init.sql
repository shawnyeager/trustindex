
-- 000_init.sql
create table if not exists countries (
  iso3 text primary key,
  iso2 text,
  name text not null,
  region text,
  income_group text
);

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
