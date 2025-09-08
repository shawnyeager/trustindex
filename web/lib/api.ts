const API_BASE_URL = 'http://localhost:3001/api'

export interface Country {
  iso3: string
  name: string
  region: string | null
  latest_year: number
  latest_gti: number | null
  confidence_tier: 'A' | 'B' | 'C' | null
}

export interface Score {
  iso3: string
  year: number
  gti: number | null
  confidence_tier: 'A' | 'B' | 'C' | null
}

export interface CountryDetail {
  iso3: string
  name: string
  region: string | null
  series: Array<{
    year: number
    gti: number | null
    interpersonal: number | null
    institutional: number | null
    governance: number | null
    confidence_tier: 'A' | 'B' | 'C' | null
    confidence_score: number | null
  }>
  sources_used?: Record<string, string[]>
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function fetchApi<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`)
  
  if (!response.ok) {
    throw new ApiError(response.status, `HTTP error! status: ${response.status}`)
  }
  
  return response.json()
}

export const api = {
  async getCountries(): Promise<Country[]> {
    return fetchApi<Country[]>('/countries')
  },
  
  async getScores(year?: number, trustType: string = 'core'): Promise<Score[]> {
    const params = new URLSearchParams()
    if (year) params.set('year', year.toString())
    params.set('trust_type', trustType)
    
    return fetchApi<Score[]>(`/score?${params}`)
  },
  
  async getCountryDetail(iso3: string, from?: number, to?: number): Promise<CountryDetail> {
    const params = new URLSearchParams()
    if (from) params.set('from', from.toString())
    if (to) params.set('to', to.toString())
    
    const query = params.toString() ? `?${params}` : ''
    return fetchApi<CountryDetail>(`/country/${iso3}${query}`)
  },
  
  async getMethodology(): Promise<any> {
    return fetchApi<any>('/methodology')
  }
}

export { ApiError }