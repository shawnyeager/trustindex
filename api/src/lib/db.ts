import { Pool } from 'pg'

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  database: process.env.POSTGRES_DB || 'trust',
  user: process.env.POSTGRES_USER || 'trust',
  password: process.env.POSTGRES_PASSWORD || 'trust',
})

export default pool