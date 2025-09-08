import Fastify from 'fastify'
import cors from '@fastify/cors'
import 'dotenv/config'

// Import routes
import countriesRoute from './routes/countries'
import scoreRoute from './routes/score'
import countryRoute from './routes/country'
import methodologyRoute from './routes/methodology'

const server = Fastify({
  logger: {
    level: process.env.NODE_ENV === 'development' ? 'info' : 'warn'
  }
})

// Register plugins
server.register(cors, {
  origin: process.env.NODE_ENV === 'development' ? ['http://localhost:3000'] : false
})

// Health check endpoint
server.get('/health', async (request, reply) => {
  return { status: 'ok', version: '0.1.0' }
})

// Register API routes
server.register(async function (fastify) {
  await fastify.register(countriesRoute, { prefix: '/api' })
  await fastify.register(scoreRoute, { prefix: '/api' })
  await fastify.register(countryRoute, { prefix: '/api' })
  await fastify.register(methodologyRoute, { prefix: '/api' })
})

// Error handler
server.setErrorHandler((error, request, reply) => {
  request.log.error(error)
  
  if (error.validation) {
    reply.status(400).send({
      error: 'Validation failed',
      details: error.validation
    })
  } else {
    reply.status(500).send({
      error: 'Internal server error'
    })
  }
})

const start = async () => {
  try {
    const port = parseInt(process.env.API_PORT || '3001')
    const host = process.env.NODE_ENV === 'development' ? '0.0.0.0' : 'localhost'
    
    await server.listen({ port, host })
    console.log(`🚀 API server ready at http://${host}:${port}`)
    console.log(`📊 Health check: http://${host}:${port}/health`)
    console.log(`📋 API endpoints: http://${host}:${port}/api/`)
    
  } catch (err) {
    server.log.error(err)
    process.exit(1)
  }
}

// Handle shutdown gracefully
const gracefulShutdown = async (signal: string) => {
  console.log(`\nReceived ${signal}, shutting down gracefully...`)
  await server.close()
  process.exit(0)
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'))
process.on('SIGINT', () => gracefulShutdown('SIGINT'))

start()