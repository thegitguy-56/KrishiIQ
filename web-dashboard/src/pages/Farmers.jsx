import { useEffect, useState } from 'react'
import { Search, MapPin, Wheat, X, Activity, Info, AlertTriangle } from 'lucide-react'
import { dashboardApi, cropApi } from '../services/api'
import toast from 'react-hot-toast'

export default function Farmers() {
  const [farmers, setFarmers] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedFarmer, setSelectedFarmer] = useState(null)
  const [predictingId, setPredictingId] = useState(null)
  const [predictionResults, setPredictionResults] = useState({})

  useEffect(() => {
    dashboardApi
      .getFarmers()
      .then((res) => {
        setFarmers(Array.isArray(res.data) ? res.data : [])
      })
      .catch((err) => toast.error(err.response?.data?.detail || 'Failed to load farmers — check API is running'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = farmers.filter((f) => {
    const name = f.name || ''
    const district = f.district || ''
    return (
      name.toLowerCase().includes(search.toLowerCase()) ||
      district.toLowerCase().includes(search.toLowerCase())
    )
  })

  const handlePredictYield = async (cropId) => {
    setPredictingId(cropId)
    try {
      const res = await cropApi.predictYield(cropId)
      setPredictionResults(prev => ({ ...prev, [cropId]: res.data }))
      toast.success('Yield prediction generated successfully')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Prediction failed. Check permissions or data.')
    } finally {
      setPredictingId(null)
    }
  }

  return (
    <div className="space-y-6 relative">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Farmers</h1>
        <span className="text-sm text-gray-500">{farmers.length} registered</span>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search by name or district…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>

      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading farmers…</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Farmer</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">District</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Farms</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Area (ac)</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Crops</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Status</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((farmer) => (
                <tr key={farmer.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{farmer.name}</td>
                  <td className="px-6 py-4 text-gray-600">
                    <span className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-gray-400" />
                      {farmer.district}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-600">{farmer.farms}</td>
                  <td className="px-6 py-4 text-gray-600">{farmer.area}</td>
                  <td className="px-6 py-4 text-gray-600">
                    <span className="flex items-center gap-1.5">
                      <Wheat className="w-3.5 h-3.5 text-gray-400" />
                      {farmer.crop}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {farmer.status === 'alert' ? (
                      <span className="badge-high">ALERT</span>
                    ) : (
                      <span className="badge-low">HEALTHY</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <button 
                      onClick={() => setSelectedFarmer(farmer)} 
                      className="text-brand-600 hover:text-brand-800 font-medium"
                    >
                      Yield Tools
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedFarmer && (
        <div className="fixed inset-0 bg-black/60 z-50 flex flex-col items-center justify-center p-4">
          <div className="bg-white w-full max-w-2xl rounded-2xl shadow-xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50">
              <div>
                <h3 className="font-semibold text-lg text-gray-900">{selectedFarmer.name}'s Crops</h3>
                <p className="text-sm text-gray-500">Select a crop to predict yield</p>
              </div>
              <button 
                onClick={() => setSelectedFarmer(null)}
                className="text-gray-400 hover:text-gray-600 p-2 rounded-full hover:bg-gray-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto">
              {!selectedFarmer.crops_data || selectedFarmer.crops_data.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Wheat className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p>No active crops found for this farmer.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {selectedFarmer.crops_data.map(crop => {
                    const prediction = predictionResults[crop.id]
                    return (
                      <div key={crop.id} className="border border-gray-200 rounded-xl p-5 hover:border-brand-200 transition-colors">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-semibold text-lg text-gray-900 flex items-center gap-2">
                            <Wheat className="w-5 h-5 text-brand-500" />
                            {crop.name}
                          </h4>
                          <button
                            onClick={() => handlePredictYield(crop.id)}
                            disabled={predictingId === crop.id}
                            className="btn-primary py-2 px-4 text-sm flex items-center gap-2 disabled:opacity-70"
                          >
                            {predictingId === crop.id ? (
                              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                              <Activity className="w-4 h-4" />
                            )}
                            Predict Yield
                          </button>
                        </div>

                        {prediction && (
                          <div className="bg-brand-50 rounded-lg p-4 border border-brand-100 mt-4 animate-in fade-in slide-in-from-top-4">
                            <div className="flex items-center gap-3 mb-3">
                              <span className="font-semibold text-brand-900">Prediction Results</span>
                              {prediction.prediction_method === 'ml_model' ? (
                                <span className="text-xs bg-brand-100 text-brand-700 px-2 py-1 rounded-full font-medium flex items-center gap-1">
                                  <Activity className="w-3 h-3" /> AI Prediction
                                </span>
                              ) : (
                                <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full font-medium flex items-center gap-1">
                                  <Info className="w-3 h-3" /> Estimated
                                </span>
                              )}
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4 mb-4">
                              <div className="bg-white p-3 rounded-md border border-brand-100">
                                <div className="text-sm text-gray-500 mb-1">Total Yield</div>
                                <div className="font-bold text-lg text-gray-900">{Math.round(prediction.predicted_yield_kg).toLocaleString()} kg</div>
                              </div>
                              <div className="bg-white p-3 rounded-md border border-brand-100">
                                <div className="text-sm text-gray-500 mb-1">Per Acre</div>
                                <div className="font-bold text-lg text-gray-900">{Math.round(prediction.yield_per_acre_kg).toLocaleString()} kg</div>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                              <Activity className="w-4 h-4 text-gray-400" />
                              Confidence: <span className="font-medium text-gray-900">{(prediction.confidence_percent * 100).toFixed(0)}%</span>
                            </div>

                            {prediction.limiting_factors?.length > 0 && (
                              <div className="mt-3 bg-red-50 p-3 rounded-md border border-red-100">
                                <div className="flex items-center gap-1.5 text-red-800 font-medium text-sm mb-2">
                                  <AlertTriangle className="w-4 h-4" /> Limiting Factors
                                </div>
                                <ul className="list-disc pl-5 text-sm text-red-700 space-y-1">
                                  {prediction.limiting_factors.map((f, i) => (
                                    <li key={i}>{f}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
