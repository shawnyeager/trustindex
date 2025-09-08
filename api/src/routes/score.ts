import { FastifyPluginAsync } from 'fastify'
import db from '../lib/db'
import { scoreQuerySchema, scoreSchema } from '../lib/schemas'

const scoreRoute: FastifyPluginAsync = async (fastify) => {
  fastify.get('/score', async (request, reply) => {
    try {
      const { year, trust_type } = scoreQuerySchema.parse(request.query)
      
      // Default to latest year if not specified
      let targetYear = year
      if (!targetYear) {
        const latestYearResult = await db.query('SELECT MAX(year) as max_year FROM country_year')
        targetYear = latestYearResult.rows[0]?.max_year || new Date().getFullYear()
      }

      // Determine which column to return based on trust_type
      let scoreColumn = 'gti'
      if (trust_type === 'interpersonal') scoreColumn = 'interpersonal'
      else if (trust_type === 'institutional') scoreColumn = 'institutional' 
      else if (trust_type === 'governance' || trust_type === 'proxy') scoreColumn = 'governance'

      const result = await db.query(`
        SELECT 
          cy.iso3,
          cy.year,
          cy.${scoreColumn} as score,
          cy.confidence_tier
        FROM country_year cy
        JOIN countries c ON cy.iso3 = c.iso3
        WHERE cy.year = $1 AND cy.${scoreColumn} IS NOT NULL
        ORDER BY c.name
      `, [targetYear])

      const scores = result.rows.map(row => ({
        iso3: row.iso3,
        year: parseInt(row.year),
        gti: row.score ? parseFloat(row.score) : null,
        confidence_tier: row.confidence_tier
      }))

      reply
        .header('Cache-Control', 's-maxage=86400, stale-while-revalidate=604800')
        .header('X-GTI-Version', '0.1.0')
        .send(scores)

    } catch (error) {
      request.log.error(error)
      reply.status(500).send({ error: 'Internal server error' })
    }
  })
}

export default scoreRoute