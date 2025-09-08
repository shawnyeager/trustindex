'use client'

import { useStore } from '@/lib/store'
import { ChevronLeft, ChevronRight } from 'lucide-react'

export default function YearSlider() {
  const { selectedYear, setSelectedYear } = useStore()
  
  // Available years (will be dynamic based on data)
  const availableYears = [2020, 2021, 2022, 2023, 2024]
  const minYear = Math.min(...availableYears)
  const maxYear = Math.max(...availableYears)
  
  const handlePrevious = () => {
    const currentIndex = availableYears.indexOf(selectedYear)
    if (currentIndex > 0) {
      setSelectedYear(availableYears[currentIndex - 1])
    }
  }
  
  const handleNext = () => {
    const currentIndex = availableYears.indexOf(selectedYear)
    if (currentIndex < availableYears.length - 1) {
      setSelectedYear(availableYears[currentIndex + 1])
    }
  }
  
  return (
    <div className="flex items-center space-x-4 bg-white px-4 py-2 rounded-lg shadow-sm border">
      <button
        onClick={handlePrevious}
        disabled={selectedYear === minYear}
        className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>
      
      <div className="flex items-center space-x-3">
        <div className="relative">
          <input
            type="range"
            min={minYear}
            max={maxYear}
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="w-32 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, #0ea5e9 0%, #0ea5e9 ${
                ((selectedYear - minYear) / (maxYear - minYear)) * 100
              }%, #e5e7eb ${
                ((selectedYear - minYear) / (maxYear - minYear)) * 100
              }%, #e5e7eb 100%)`
            }}
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{minYear}</span>
            <span>{maxYear}</span>
          </div>
        </div>
        
        <div className="text-lg font-semibold text-gray-900 min-w-[4rem] text-center">
          {selectedYear}
        </div>
      </div>
      
      <button
        onClick={handleNext}
        disabled={selectedYear === maxYear}
        className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  )
}