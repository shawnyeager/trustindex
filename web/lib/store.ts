import { create } from 'zustand'

export type TrustMode = 'core' | 'interpersonal' | 'institutional' | 'governance'
export type ColorScale = 'quantiles' | 'continuous' | 'diverging'

interface Country {
  iso3: string
  name: string
  region: string | null
  latest_year: number
  latest_gti: number | null
  confidence_tier: 'A' | 'B' | 'C' | null
}

interface CountryDetail {
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

interface AppState {
  // Map state
  selectedYear: number
  trustMode: TrustMode
  colorScale: ColorScale
  overlays: {
    regionalBarometers: boolean
    edelman: boolean
    cpi: boolean
    wgi: boolean
    oecd: boolean
    pew: boolean
  }
  
  // Data
  countries: Country[]
  selectedCountry: string | null
  countryDetail: CountryDetail | null
  scores: Array<{
    iso3: string
    year: number
    gti: number | null
    confidence_tier: 'A' | 'B' | 'C' | null
  }>
  
  // Loading states
  isLoading: boolean
  isLoadingCountryDetail: boolean
  
  // Actions
  setSelectedYear: (year: number) => void
  setTrustMode: (mode: TrustMode) => void
  setColorScale: (scale: ColorScale) => void
  toggleOverlay: (overlay: keyof AppState['overlays']) => void
  setCountries: (countries: Country[]) => void
  setSelectedCountry: (iso3: string | null) => void
  setCountryDetail: (detail: CountryDetail | null) => void
  setScores: (scores: AppState['scores']) => void
  setLoading: (loading: boolean) => void
  setLoadingCountryDetail: (loading: boolean) => void
}

export const useStore = create<AppState>()((set, get) => ({
  // Initial state
  selectedYear: new Date().getFullYear(),
  trustMode: 'core',
  colorScale: 'quantiles',
  overlays: {
    regionalBarometers: false,
    edelman: false,
    cpi: false,
    wgi: false,
    oecd: false,
    pew: false
  },
  
  countries: [],
  selectedCountry: null,
  countryDetail: null,
  scores: [],
  
  isLoading: false,
  isLoadingCountryDetail: false,
  
  // Actions
  setSelectedYear: (year) => set({ selectedYear: year }),
  setTrustMode: (mode) => set({ trustMode: mode }),
  setColorScale: (scale) => set({ colorScale: scale }),
  toggleOverlay: (overlay) => set((state) => ({
    overlays: {
      ...state.overlays,
      [overlay]: !state.overlays[overlay]
    }
  })),
  setCountries: (countries) => set({ countries }),
  setSelectedCountry: (iso3) => set({ selectedCountry: iso3 }),
  setCountryDetail: (detail) => set({ countryDetail: detail }),
  setScores: (scores) => set({ scores }),
  setLoading: (loading) => set({ isLoading: loading }),
  setLoadingCountryDetail: (loading) => set({ isLoadingCountryDetail: loading })
}))