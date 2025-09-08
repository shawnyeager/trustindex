import { FastifyPluginAsync } from 'fastify'
import db from '../lib/db'
import { countryQuerySchema, countryDetailSchema } from '../lib/schemas'

const countryRoute: FastifyPluginAsync = async (fastify) => {
  fastify.get('/country/:iso3', async (request, reply) => {
    try {
      const { iso3 } = request.params as { iso3: string }
      const { from, to } = countryQuerySchema.parse(request.query)

      // Get country info
      const countryResult = await db.query(`
        SELECT iso3, name, region FROM countries WHERE iso3 = $1
      `, [iso3])

      if (countryResult.rows.length === 0) {
        return reply.status(404).send({ error: 'Country not found' })
      }

      const country = countryResult.rows[0]

      // Build year filter
      let yearFilter = ''
      const queryParams = [iso3]
      
      if (from && to) {
        yearFilter = 'AND year BETWEEN $2 AND $3'
        queryParams.push(from, to)
      } else if (from) {
        yearFilter = 'AND year >= $2'
        queryParams.push(from)
      } else if (to) {
        yearFilter = 'AND year <= $2'
        queryParams.push(to)
      }

      // Get time series data
      const seriesResult = await db.query(`
        SELECT 
          year,
          gti,
          interpersonal,
          institutional,
          governance,
          confidence_tier,
          confidence_score,
          sources_used
        FROM country_year 
        WHERE iso3 = $1 ${yearFilter}
        ORDER BY year DESC
      `, queryParams)

      const series = seriesResult.rows.map(row => ({
        year: parseInt(row.year),
        gti: row.gti ? parseFloat(row.gti) : null,
        interpersonal: row.interpersonal ? parseFloat(row.interpersonal) : null,
        institutional: row.institutional ? parseFloat(row.institutional) : null,
        governance: row.governance ? parseFloat(row.governance) : null,
        confidence_tier: row.confidence_tier,
        confidence_score: row.confidence_score ? parseFloat(row.confidence_score) : null
      }))

      // Aggregate sources_used across all years
      const allSources = seriesResult.rows
        .filter(row => row.sources_used)
        .reduce((acc, row) => {
          const sources = JSON.parse(row.sources_used)
          Object.keys(sources).forEach(pillar => {
            if (!acc[pillar]) acc[pillar] = new Set()
            sources[pillar].forEach((source: string) => acc[pillar].add(source))
          })
          return acc
        }, {} as Record<string, Set<string>>)

      const sourcesUsed = Object.fromEntries(
        Object.entries(allSources).map(([pillar, sourceSet]) => [
          pillar,
          Array.from(sourceSet)
        ])
      )

      const response = {
        iso3: country.iso3,
        name: country.name,
        region: country.region,
        series,
        sources_used: sourcesUsed
      }

      reply
        .header('Cache-Control', 's-maxage=86400, stale-while-revalidate=604800')
        .header('X-GTI-Version', '0.1.0')
        .send(response)

    } catch (error) {
      request.log.error(error)
      reply.status(500).send({ error: 'Internal server error' })
    }
  })
}

export default countryRoute