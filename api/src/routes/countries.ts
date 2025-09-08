import { FastifyPluginAsync } from 'fastify'
import db from '../lib/db'
import { countrySchema, countryResponseSchema } from '../lib/schemas'

const countriesRoute: FastifyPluginAsync = async (fastify) => {
  fastify.get('/countries', async (request, reply) => {
    try {
      const result = await db.query(`
        SELECT 
          c.iso3,
          c.name,
          c.region,
          cy.year as latest_year,
          cy.gti as latest_gti,
          cy.confidence_tier
        FROM countries c
        LEFT JOIN country_year cy ON c.iso3 = cy.iso3
        LEFT JOIN (
          SELECT iso3, MAX(year) as max_year
          FROM country_year
          GROUP BY iso3
        ) latest ON c.iso3 = latest.iso3 AND cy.year = latest.max_year
        ORDER BY c.name
      `)

      const countries = result.rows.map(row => ({
        iso3: row.iso3,
        name: row.name,
        region: row.region,
        latest_year: row.latest_year || null,
        latest_gti: row.latest_gti ? parseFloat(row.latest_gti) : null,
        confidence_tier: row.confidence_tier
      }))

      reply
        .header('Cache-Control', 's-maxage=86400, stale-while-revalidate=604800')
        .header('X-GTI-Version', '0.1.0')
        .send(countries)

    } catch (error) {
      request.log.error(error)
      reply.status(500).send({ error: 'Internal server error' })
    }
  })
}

export default countriesRoute