'use client'

import { useStore } from '@/lib/store'

export default function FilterPanel() {
  const {
    trustMode,
    colorScale,
    overlays,
    setTrustMode,
    setColorScale,
    toggleOverlay
  } = useStore()

  return (
    <div className="w-80 bg-white border-r border-gray-200 p-6 overflow-y-auto">
      {/* MODE Section */}
      <div className="filter-group">
        <h3 className="filter-label">Mode</h3>
        <div className="space-y-3">
          <label className="filter-option">
            <input
              type="radio"
              name="mode"
              value="core"
              checked={trustMode === 'core'}
              onChange={(e) => setTrustMode(e.target.value as any)}
              className="w-4 h-4 text-trust-600 border-gray-300 focus:ring-trust-500"
            />
            <div>
              <div className="font-medium text-gray-900">Core Trust Score</div>
              <div className="text-xs text-gray-500">(Gallup + WVS)</div>
            </div>
          </label>
          
          <label className="filter-option">
            <input
              type="radio"
              name="mode"
              value="interpersonal"
              checked={trustMode === 'interpersonal'}
              onChange={(e) => setTrustMode(e.target.value as any)}
              className="w-4 h-4 text-trust-600 border-gray-300 focus:ring-trust-500"
            />
            <div className="font-medium text-gray-900">Interpersonal (WVS)</div>
          </label>
          
          <label className="filter-option">
            <input
              type="radio"
              name="mode"
              value="governance"
              checked={trustMode === 'governance'}
              onChange={(e) => setTrustMode(e.target.value as any)}
              className="w-4 h-4 text-trust-600 border-gray-300 focus:ring-trust-500"
            />
            <div className="font-medium text-gray-900">Govt Trust (Gallup)</div>
          </label>
        </div>
      </div>

      {/* OVERLAYS Section */}
      <div className="filter-group">
        <h3 className="filter-label">Overlays</h3>
        <div className="space-y-2">
          {Object.entries({
            regionalBarometers: 'Regional barometers',
            edelman: 'Edelman',
            cpi: 'CPI',
            wgi: 'WGI',
            oecd: 'OECD',
            pew: 'Pew'
          }).map(([key, label]) => (
            <label key={key} className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={overlays[key as keyof typeof overlays]}
                onChange={() => toggleOverlay(key as keyof typeof overlays)}
                className="w-4 h-4 text-trust-600 border-gray-300 rounded focus:ring-trust-500"
              />
              <span className="text-gray-600">{label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* COLOR SCALE Section */}
      <div className="filter-group">
        <h3 className="filter-label">Color Scale</h3>
        <div className="space-y-2">
          {[
            { value: 'quantiles', label: 'Quantiles' },
            { value: 'continuous', label: 'Continuous' },
            { value: 'diverging', label: 'Diverging' }
          ].map((option) => (
            <label key={option.value} className="filter-option">
              <input
                type="radio"
                name="colorScale"
                value={option.value}
                checked={colorScale === option.value}
                onChange={(e) => setColorScale(e.target.value as any)}
                className="w-4 h-4 text-trust-600 border-gray-300 focus:ring-trust-500"
              />
              <span className="text-gray-900">{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Data Attribution */}
      <div className="mt-8 text-xs text-gray-500 border-t pt-4">
        <div className="font-medium mb-1">Data: WVS, Gallup</div>
      </div>
    </div>
  )
}