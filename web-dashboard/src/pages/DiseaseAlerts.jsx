import { useEffect, useState } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { diseaseApi, dashboardApi } from '../services/api'
import toast from 'react-hot-toast'

export default function DiseaseAlerts() {
  const [alerts, setAlerts] = useState([])
  const [districts, setDistricts] = useState([])
  const [district, setDistrict] = useState('')
  const [severity, setSeverity] = useState('high')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    dashboardApi.getDistricts()
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

  const fetchAlerts = () => {
    if (!district) return
    setLoading(true)
    diseaseApi.getDistrictAlerts(district, severity)
      .then((res) => setAlerts(res.data))
      .catch((err) => toast.error(err.response?.data?.detail || 'Failed to fetch alerts'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (district) fetchAlerts()
  }, [district, severity])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Disease Alerts</h1>
        <button onClick={fetchAlerts} className="btn-secondary flex items-center gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="flex gap-4 flex-wrap">
        <select
          value={district}
          onChange={(e) => setDistrict(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          {districts.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="high">High & Critical only</option>
          <option value="medium">Medium & above</option>
        </select>
      </div>

      {loading ? (
        <div className="text-gray-400 text-center py-12">Loading alerts…</div>
      ) : alerts.length === 0 ? (
        <div className="card text-center py-12">
          <AlertTriangle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No {severity} severity alerts in {district}</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {alerts.map((alert) => (
            <div key={alert.id} className="card flex items-start gap-4">
              <div className={`mt-0.5 w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                alert.severity === 'critical' ? 'bg-red-100' : 'bg-orange-100'
              }`}>
                <AlertTriangle className={`w-5 h-5 ${alert.severity === 'critical' ? 'text-red-600' : 'text-orange-600'}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-gray-900">{alert.detected_disease || 'Unknown disease'}</span>
                  <span className={`badge-${alert.severity}`}>{alert.severity?.toUpperCase()}</span>
                  {alert.is_pest_anomaly === 'true' && (
                    <span className="bg-purple-100 text-purple-700 text-xs font-semibold px-2 py-0.5 rounded-full">PEST ANOMALY</span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">{alert.treatment_recommendation}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                  <span>Confidence: {((alert.confidence_score || 0) * 100).toFixed(1)}%</span>
                  <span>Affected: {alert.affected_area_percent?.toFixed(1)}%</span>
                  <span>{new Date(alert.created_at).toLocaleString('en-IN')}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
