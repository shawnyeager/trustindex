import { z } from 'zod'

// Query parameter schemas
export const scoreQuerySchema = z.object({
  year: z.string().regex(/^\d{4}$/).transform(Number).optional(),
  trust_type: z.enum(['core', 'interpersonal', 'institutional', 'governance', 'proxy']).default('core')
})

export const countryQuerySchema = z.object({
  from: z.string().regex(/^\d{4}$/).transform(Number).optional(),
  to: z.string().regex(/^\d{4}$/).transform(Number).optional()
})

// Response schemas
export const countrySchema = z.object({
  iso3: z.string(),
  name: z.string(),
  region: z.string().nullable(),
  latest_year: z.number(),
  latest_gti: z.number().nullable(),
  confidence_tier: z.enum(['A', 'B', 'C']).nullable()
})

export const countryResponseSchema = {
  type: 'object',
  required: ['iso3', 'name'],
  properties: {
    iso3: { type: 'string' },
    name: { type: 'string' },
    region: { type: ['string', 'null'] },
    latest_year: { type: 'number' },
    latest_gti: { type: ['number', 'null'] },
    confidence_tier: { type: ['string', 'null'], enum: ['A', 'B', 'C', null] }
  }
}

export const scoreSchema = z.object({
  iso3: z.string(),
  year: z.number(),
  gti: z.number().nullable(),
  confidence_tier: z.enum(['A', 'B', 'C']).nullable()
})

export const countryDetailSchema = z.object({
  iso3: z.string(),
  name: z.string(),
  region: z.string().nullable(),
  series: z.array(z.object({
    year: z.number(),
    gti: z.number().nullable(),
    interpersonal: z.number().nullable(),
    institutional: z.number().nullable(),
    governance: z.number().nullable(),
    confidence_tier: z.enum(['A', 'B', 'C']).nullable(),
    confidence_score: z.number().nullable()
  })),
  sources_used: z.record(z.array(z.string())).optional()
})

export type Country = z.infer<typeof countrySchema>
export type Score = z.infer<typeof scoreSchema>
export type CountryDetail = z.infer<typeof countryDetailSchema>