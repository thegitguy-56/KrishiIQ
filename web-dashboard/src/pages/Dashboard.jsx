import { useEffect, useState } from 'react'
import { Users, Wheat, AlertTriangle, Droplets } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, Legend } from 'recharts'
import StatCard from '../components/Common/StatCard'
import { dashboardApi } from '../services/api'
import toast from 'react-hot-toast'

export default function Dashboard() {
  const [overview, setOverview] = useState(null)
  const [heatmap, setHeatmap] = useState([])
  const [yieldTrends, setYieldTrends] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      dashboardApi.getOverview(),
      dashboardApi.getDistrictHeatmap(),
      dashboardApi.getYieldTrends(),
    ])
      .then(([ovRes, hmRes, yieldRes]) => {
        setOverview(ovRes.data)
        setHeatmap(hmRes.data)
        setYieldTrends(yieldRes.data || [])
      })
      .catch((err) => {
        console.error(err)
        toast.error(err.response?.data?.detail || 'Failed to load dashboard — is the API running on port 8000?')
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Loading dashboard…
      </div>
    )
  }

  const stats = overview || { total_farmers: 0, total_farms: 0, total_area_acres: 0, active_crops: 0 }
  const yieldKeys = yieldTrends.length
    ? Object.keys(yieldTrends[0]).filter((k) => k !== 'month')
    : []

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">District Overview</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Total Farmers" value={stats.total_farmers.toLocaleString()} icon={Users} color="brand" />
        <StatCard title="Total Farms" value={stats.total_farms.toLocaleString()} icon={Wheat} color="orange" />
        <StatCard title="Area (Acres)" value={stats.total_area_acres.toLocaleString()} icon={Droplets} color="blue" />
        <StatCard
          title="Active Disease Alerts"
          value={stats.recent_disease_alerts?.length || 0}
          icon={AlertTriangle}
          color="red"
          subtitle="High/Critical severity"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Crop Yield Trends (kg/acre)</h2>
          {yieldTrends.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={yieldTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                {yieldKeys.map((key, i) => (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stroke={['#16a34a', '#d97706', '#2563eb'][i % 3]}
                    strokeWidth={2}
                    dot={false}
                    name={key.replace(/_/g, ' ')}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-sm py-16 text-center">No crop yield data yet — add crop records via mobile app</p>
          )}
        </div>

        <div className="card">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Farm Count by District</h2>
          {heatmap.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={heatmap.slice(0, 8)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="district" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="farm_count" fill="#16a34a" radius={[4, 4, 0, 0]} name="Farms" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-sm py-16 text-center">No district data available</p>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Recent Disease Alerts</h2>
        {stats.recent_disease_alerts?.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-100">
                <th className="pb-2 font-medium">Disease</th>
                <th className="pb-2 font-medium">Severity</th>
                <th className="pb-2 font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_disease_alerts.map((alert, i) => (
                <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2.5 font-medium text-gray-900">{alert.disease}</td>
                  <td className="py-2.5">
                    <span className={`badge-${alert.severity}`}>{alert.severity.toUpperCase()}</span>
                  </td>
                  <td className="py-2.5 text-gray-500">{new Date(alert.date).toLocaleDateString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-gray-400 text-sm">No recent high-severity alerts</p>
        )}
      </div>
    </div>
  )
}
