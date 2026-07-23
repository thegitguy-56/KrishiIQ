import { useEffect, useState } from 'react'
import { Search, MapPin, Wheat } from 'lucide-react'
import { dashboardApi } from '../services/api'
import toast from 'react-hot-toast'

export default function Farmers() {
  const [farmers, setFarmers] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    dashboardApi
      .getFarmers()
      .then((res) => {
  console.log('STATUS:', res.status)
  console.log('DATA:', res.data)
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

  return (
    <div className="space-y-6">
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
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
