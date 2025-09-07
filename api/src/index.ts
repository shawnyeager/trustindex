
import Fastify from 'fastify';
import { Pool } from 'pg';

const PORT = parseInt(process.env.API_PORT || '3001', 10);
const POSTGRES_URL = process.env.POSTGRES_URL || 'postgresql://trust:trust@localhost:5432/trust';

const fastify = Fastify({ logger: true });
const pool = new Pool({ connectionString: POSTGRES_URL });

fastify.get('/api/countries', async (req, reply) => {
  const { rows } = await pool.query('select iso3, name, region from countries order by name asc');
  return rows;
});

// Mock core score endpoint (returns proxy-only using observations if present; else demo data)
fastify.get('/api/score', async (req, reply) => {
  const year = Number((req.query as any).year ?? new Date().getFullYear());
  const trust_type = (req.query as any).trust_type ?? 'core';
  const { rows } = await pool.query("""
    with latest as (
      select c.iso3, c.name
      from countries c
    )
    select l.iso3, l.name, 50 + (abs(mod((ascii(l.iso3)-65)*7 + $1, 40))::int) as gti, $1 as year
    from latest l
  """, [year]);
  return rows;
});

fastify.get('/api/country/:iso3', async (req, reply) => {
  const iso3 = (req.params as any).iso3;
  const series = [
    { year: 2020, gti: 55, inter: 48, inst: 60, gov: 57 },
    { year: 2021, gti: 58, inter: 49, inst: 62, gov: 60 },
    { year: 2022, gti: 60, inter: 50, inst: 63, gov: 62 },
    { year: 2023, gti: 62, inter: 51, inst: 65, gov: 63 },
  ];
  return { iso3, series, sources_used: ["CPI", "WGI"], confidence: ["B","B","A","A"] };
});

fastify.listen({ port: PORT, host: '0.0.0.0' });
