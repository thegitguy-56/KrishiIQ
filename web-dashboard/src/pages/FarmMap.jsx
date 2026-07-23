import { useEffect, useState, useMemo } from 'react'
import { dashboardApi, aiApi } from '../services/api'
import toast from 'react-hot-toast'
import FarmMapLeaflet from '../components/FarmMapLeaflet'
import FarmMapGoogle from '../components/FarmMapGoogle'

const defaultCenter = { lat: 11.0168, lng: 76.9558 }

export default function FarmMap() {
  const [farms, setFarms] = useState([])
  const [riskData, setRiskData] = useState([])
  const [districts, setDistricts] = useState([])
  const [district, setDistrict] = useState('')
  const [mapsKey, setMapsKey] = useState('')
  const [configReady, setConfigReady] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const envKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY?.trim()
    if (envKey) {
      setMapsKey(envKey)
      setConfigReady(true)
      return
    }
    aiApi
      .getPublicConfig()
      .then((res) => {
        const key = res.data?.google_maps_api_key?.trim()
        if (key) setMapsKey(key)
      })
      .catch(() => {})
      .finally(() => setConfigReady(true))

    dashboardApi
      .getDistricts()
      .then((res) => {
        const list = res.data?.length ? res.data : ['Coimbatore']
        setDistricts(list)
        setDistrict(list[0])
      })
      .catch(() => {
        setDistricts(['Coimbatore'])
        setDistrict('Coimbatore')
      })
  }, [])

  useEffect(() => {
    if (!district) return
    setLoading(true)
    Promise.all([
      dashboardApi.getFarmsMap(district),
      dashboardApi.getPestSpreadRisk(district),
    ])
      .then(([mapRes, riskRes]) => {
        setFarms(mapRes.data.farms || [])
        setRiskData(riskRes.data.risk_assessments || [])
      })
      .catch((err) => {
        const msg = err.response?.data?.detail || err.message || 'Failed to load farm map'
        toast.error(typeof msg === 'string' ? msg : 'Failed to load farm map — is API on port 8001?')
      })
      .finally(() => setLoading(false))
  }, [district])

  const useGoogle = Boolean(mapsKey)
  const riskIds = useMemo(() => new Set(riskData.map((r) => r.farm_id)), [riskData])

  const center = farms.length
    ? { lat: farms[0].lat, lng: farms[0].lon }
    : defaultCenter

  const districtOptions = districts.length ? districts : [district || 'Coimbatore']

  if (!configReady) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">Loading map configuration…</div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Farm Map — {district || '…'} District</h1>
        <select
          value={district}
          onChange={(e) => setDistrict(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
        >
          {districtOptions.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 bg-green-500 rounded-full inline-block" /> Healthy
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 bg-red-500 rounded-full inline-block" /> Infected
          </span>
        </div>
      </div>

      {!useGoogle && (
        <div className="bg-blue-50 border border-blue-100 text-blue-800 text-sm rounded-lg px-4 py-2">
          Using OpenStreetMap (no Google API key). Add <code className="bg-blue-100 px-1 rounded">VITE_GOOGLE_MAPS_API_KEY</code> in{' '}
          <code className="bg-blue-100 px-1 rounded">web-dashboard/.env.local</code> or{' '}
          <code className="bg-blue-100 px-1 rounded">GOOGLE_MAPS_API_KEY</code> in <code className="bg-blue-100 px-1 rounded">backend/.env.local</code> for Google Maps.
        </div>
      )}

      <div className="card p-0 overflow-hidden rounded-xl">
        {loading ? (
          <div className="flex items-center justify-center h-[580px] text-gray-500">Loading farms…</div>
        ) : farms.length === 0 ? (
          <div className="flex items-center justify-center h-[580px] text-gray-500">No farms in this district</div>
        ) : useGoogle ? (
          <FarmMapGoogle mapsKey={mapsKey} farms={farms} riskData={riskData} center={center} />
        ) : (
          <FarmMapLeaflet farms={farms} riskIds={riskIds} center={center} />
        )}
      </div>
    </div>
  )
}
