'use client'

import { useEffect, useRef, useState } from 'react'
import { useStore } from '@/lib/store'

// Mock map component for MVP - will replace with actual Mapbox implementation
export default function MapView() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const { selectedCountry, scores, trustMode, setSelectedCountry } = useStore()
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null)

  // Mock country polygons for demonstration
  const mockCountries = [
    { iso3: 'SWE', name: 'Sweden', score: 74, x: 60, y: 30, color: '#22c55e' },
    { iso3: 'USA', name: 'United States', score: 69, x: 25, y: 40, color: '#84cc16' },
    { iso3: 'BRA', name: 'Brazil', score: 38, x: 30, y: 70, color: '#f59e0b' },
    { iso3: 'NGA', name: 'Nigeria', score: 25, x: 52, y: 65, color: '#ef4444' },
    { iso3: 'IND', name: 'India', score: 40, x: 70, y: 55, color: '#f59e0b' }
  ]

  const handleCountryClick = (iso3: string) => {
    setSelectedCountry(iso3 === selectedCountry ? null : iso3)
  }

  return (
    <div className="relative flex-1 bg-gray-50">
      {/* Mock World Map */}
      <div 
        ref={mapContainer}
        className="w-full h-full relative overflow-hidden"
        style={{ background: 'linear-gradient(180deg, #bfdbfe 0%, #93c5fd 100%)' }}
      >
        {/* Mock continents as simple shapes */}
        <svg 
          className="absolute inset-0 w-full h-full"
          viewBox="0 0 100 100"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Mock country shapes */}
          {mockCountries.map((country) => (
            <g key={country.iso3}>
              {/* Country polygon (simplified) */}
              <circle
                cx={country.x}
                cy={country.y}
                r="4"
                fill={country.color}
                stroke="#fff"
                strokeWidth="0.5"
                className="cursor-pointer transition-all duration-200 hover:stroke-gray-900 hover:stroke-2"
                onClick={() => handleCountryClick(country.iso3)}
                onMouseEnter={() => setHoveredCountry(country.iso3)}
                onMouseLeave={() => setHoveredCountry(null)}
              />
              
              {/* Country label */}
              <text
                x={country.x}
                y={country.y - 6}
                textAnchor="middle"
                className="text-[2px] fill-gray-700 font-medium pointer-events-none"
              >
                {country.name}
              </text>
            </g>
          ))}
        </svg>

        {/* Hover tooltip */}
        {hoveredCountry && (
          <div className="absolute pointer-events-none z-10 transform -translate-x-1/2 -translate-y-full">
            {(() => {
              const country = mockCountries.find(c => c.iso3 === hoveredCountry)
              if (!country) return null
              
              return (
                <div 
                  className="bg-gray-900 text-white px-3 py-2 rounded-lg shadow-lg"
                  style={{
                    left: `${country.x}%`,
                    top: `${country.y}%`
                  }}
                >
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-4 bg-gray-200 rounded border"></div>
                    <span className="font-medium">{country.name}</span>
                    <span className="text-yellow-400 font-bold">{country.score}</span>
                  </div>
                  <div className="text-xs text-gray-300">WVS (2022)</div>
                </div>
              )
            })()}
          </div>
        )}

        {/* Color scale legend */}
        <div className="map-legend">
          <div className="text-xs font-medium text-gray-700 mb-2">0–100</div>
          <div className="flex items-center space-x-1">
            {[
              { color: '#ef4444', label: '0' },
              { color: '#f59e0b', label: '25' },
              { color: '#84cc16', label: '50' },
              { color: '#22c55e', label: '75' },
              { color: '#16a34a', label: '100' }
            ].map((item, i) => (
              <div key={i} className="flex flex-col items-center">
                <div 
                  className="w-6 h-3"
                  style={{ backgroundColor: item.color }}
                ></div>
                {i === 0 || i === 4 ? (
                  <div className="text-xs text-gray-500 mt-1">{item.label}</div>
                ) : null}
              </div>
            ))}
          </div>
        </div>

        {/* Mock placeholder text */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="bg-white/90 p-6 rounded-lg shadow-lg max-w-md text-center">
            <h3 className="font-semibold text-gray-900 mb-2">Interactive Map Placeholder</h3>
            <p className="text-sm text-gray-600">
              This is a mockup of the choropleth map. Click on countries to see details.
              In production, this will use Mapbox GL with real vector tiles.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}