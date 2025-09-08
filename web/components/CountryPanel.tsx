'use client'

import { useEffect } from 'react'
import { useStore } from '@/lib/store'
import { api } from '@/lib/api'
import { ChevronDown, TrendingUp } from 'lucide-react'

export default function CountryPanel() {
  const {
    selectedCountry,
    countryDetail,
    isLoadingCountryDetail,
    setCountryDetail,
    setLoadingCountryDetail
  } = useStore()

  useEffect(() => {
    if (selectedCountry) {
      setLoadingCountryDetail(true)
      api.getCountryDetail(selectedCountry)
        .then(setCountryDetail)
        .catch(console.error)
        .finally(() => setLoadingCountryDetail(false))
    } else {
      setCountryDetail(null)
    }
  }, [selectedCountry, setCountryDetail, setLoadingCountryDetail])

  if (!selectedCountry) {
    return (
      <div className="w-96 bg-white border-l border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
            🌍
          </div>
          <h3 className="font-medium text-gray-900 mb-2">Select a Country</h3>
          <p className="text-sm">Click on a country on the map to see detailed trust scores and trends.</p>
        </div>
      </div>
    )
  }

  if (isLoadingCountryDetail) {
    return (
      <div className="w-96 bg-white border-l border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!countryDetail) {
    return (
      <div className="w-96 bg-white border-l border-gray-200 p-6">
        <div className="text-center text-red-500">
          <h3 className="font-medium">Error Loading Country Data</h3>
          <p className="text-sm">Please try selecting another country.</p>
        </div>
      </div>
    )
  }

  const latestData = countryDetail.series[0] // Assuming sorted by year desc
  const getFlagEmoji = (iso3: string) => {
    const flags: Record<string, string> = {
      'SWE': '🇸🇪',
      'USA': '🇺🇸', 
      'BRA': '🇧🇷',
      'NGA': '🇳🇬',
      'IND': '🇮🇳',
      'DEU': '🇩🇪',
      'JPN': '🇯🇵',
      'ZAF': '🇿🇦',
      'GBR': '🇬🇧',
      'FRA': '🇫🇷'
    }
    return flags[iso3] || '🏳️'
  }

  return (
    <div className="w-96 bg-white border-l border-gray-200 p-6 overflow-y-auto">
      {/* Country Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{getFlagEmoji(countryDetail.iso3)}</span>
          <div>
            <h2 className="text-xl font-bold text-gray-900">{countryDetail.name}</h2>
            <div className="text-sm text-gray-500">{countryDetail.region}</div>
          </div>
        </div>
        <button className="p-1 rounded hover:bg-gray-100">
          <ChevronDown className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="country-stat">
          <div className="country-stat-value">{latestData?.gti?.toFixed(0) || '–'}</div>
          <div className="country-stat-label">Core</div>
        </div>
        <div className="country-stat">
          <div className="country-stat-value">{latestData?.interpersonal?.toFixed(0) || '–'}</div>
          <div className="country-stat-label">Interper</div>
        </div>
        <div className="country-stat">
          <div className="country-stat-value">{latestData?.governance?.toFixed(0) || '–'}</div>
          <div className="country-stat-label">Govt</div>
        </div>
      </div>

      {/* Trend Chart Placeholder */}
      <div className="mb-6">
        <div className="h-32 bg-gray-50 rounded-lg flex items-center justify-center relative">
          {/* Mock trend line */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 50">
            <polyline
              points="10,40 25,35 40,30 55,32 70,28 85,25"
              fill="none"
              stroke="#0ea5e9"
              strokeWidth="2"
              className="opacity-80"
            />
            {/* Data points */}
            {[10, 25, 40, 55, 70, 85].map((x, i) => (
              <circle
                key={i}
                cx={x}
                cy={40 - i * 3}
                r="2"
                fill="#0ea5e9"
                className="opacity-80"
              />
            ))}
          </svg>
          <div className="absolute top-2 left-2 text-xs text-gray-500">2020</div>
          <div className="absolute top-2 right-2 text-xs text-gray-500 flex items-center">
            <TrendingUp className="w-3 h-3 mr-1" />
            Trending up
          </div>
        </div>
      </div>

      {/* Source Breakdown */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-900 mb-3">Source Breakdown</h3>
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm border-b pb-2">
            <span className="font-medium">Source</span>
            <span className="font-medium">Value</span>
            <span className="font-medium">Year</span>
            <span className="font-medium">Sample</span>
          </div>
          
          {/* Mock data rows */}
          <div className="text-sm text-gray-600 space-y-2">
            <div className="flex justify-between items-center">
              <span>Gallup</span>
              <span className="font-medium">{latestData?.gti?.toFixed(0) || '–'}</span>
              <span>2023</span>
              <span>1002</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Pew</span>
              <span className="font-medium">{latestData?.interpersonal?.toFixed(0) || '–'}</span>
              <span>2021</span>
              <span>995</span>
            </div>
            <div className="flex justify-between items-center">
              <span>WVS</span>
              <span className="font-medium">{latestData?.governance?.toFixed(0) || '–'}</span>
              <span>2022</span>
              <span>1250</span>
            </div>
          </div>
        </div>
      </div>

      {/* Comparisons */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-3">Comparisons</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
            <span className="text-gray-600">vs region avg</span>
            <span className="font-medium text-green-600">+12</span>
          </div>
          <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
            <span className="text-gray-600">vs income peergroup</span>
            <span className="font-medium text-green-600">+8</span>
          </div>
        </div>
      </div>
    </div>
  )
}