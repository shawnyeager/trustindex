'use client'

import { useEffect } from 'react'
import { Search, Download } from 'lucide-react'
import { useStore } from '@/lib/store'
import { api } from '@/lib/api'
import FilterPanel from '@/components/FilterPanel'
import YearSlider from '@/components/YearSlider'
import MapView from '@/components/MapView'
import CountryPanel from '@/components/CountryPanel'

export default function HomePage() {
  const { 
    selectedYear, 
    trustMode,
    setCountries, 
    setScores, 
    setLoading 
  } = useStore()

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      try {
        const [countries, scores] = await Promise.all([
          api.getCountries(),
          api.getScores(selectedYear, trustMode)
        ])
        setCountries(countries)
        setScores(scores)
      } catch (error) {
        console.error('Failed to load data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [selectedYear, trustMode, setCountries, setScores, setLoading])

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <h1 className="text-2xl font-bold text-gray-900">Trust Index</h1>
            
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search country or region"
                className="pl-9 pr-4 py-2 w-80 border border-gray-300 rounded-lg focus:ring-2 focus:ring-trust-500 focus:border-trust-500"
              />
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <YearSlider />
            
            <button className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        <FilterPanel />
        <MapView />
        <CountryPanel />
      </div>
    </div>
  )
}