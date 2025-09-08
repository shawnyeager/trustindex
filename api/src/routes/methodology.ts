import { FastifyPluginAsync } from 'fastify'
import { readFileSync } from 'fs'
import { join } from 'path'
import yaml from 'js-yaml'

const methodologyRoute: FastifyPluginAsync = async (fastify) => {
  // Load methodology YAML once at startup
  const methodologyPath = join(process.cwd(), '..', 'data', 'reference', 'methodology.yaml')
  let methodologyData: any

  try {
    const yamlContent = readFileSync(methodologyPath, 'utf8')
    methodologyData = yaml.load(yamlContent)
  } catch (error) {
    fastify.log.error('Failed to load methodology.yaml:', error)
    methodologyData = {
      version: '0.1.0',
      error: 'Methodology file not found'
    }
  }

  fastify.get('/methodology', async (request, reply) => {
    reply
      .header('Cache-Control', 's-maxage=86400, stale-while-revalidate=604800')
      .header('X-GTI-Version', methodologyData.version || '0.1.0')
      .header('Content-Type', 'application/json')
      .send(methodologyData)
  })
}

export default methodologyRoute