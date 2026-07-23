import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { dashboardApi } from '../services/api'

const COLORS = ['#16a34a', '#d97706', '#2563eb', '#dc2626', '#7c3aed']

export default function Analytics() {
  const [heatmap, setHeatmap] = useState([])
  const [waterData, setWaterData] = useState([])
  const [cropDist, setCropDist] = useState([])

  useEffect(() => {
    Promise.all([
      dashboardApi.getDistrictHeatmap(),
      dashboardApi.getWaterUsage(),
      dashboardApi.getCropDistribution(),
    ])
      .then(([hm, water, crops]) => {
        setHeatmap(hm.data)
        setWaterData(water.data)
        setCropDist(crops.data.length ? crops.data : [{ name: 'No data', value: 100 }])
      })
      .catch(() => {})
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Water Usage — Farms Needing Irrigation</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={waterData}>
              <XAxis dataKey="district" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="farms" fill="#e2e8f0" radius={[4, 4, 0, 0]} name="Total Farms (IoT)" />
              <Bar dataKey="irrigating" fill="#2563eb" radius={[4, 4, 0, 0]} name="Need Irrigation" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Crop Distribution</h2>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={cropDist}
                cx="50%"
                cy="50%"
                outerRadius={90}
                dataKey="value"
                label={({ name, value }) => `${name} ${value}%`}
                labelLine={false}
              >
                {cropDist.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card xl:col-span-2">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Total Land Area by District (Acres)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={heatmap}>
              <XAxis dataKey="district" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="total_acres" fill="#16a34a" radius={[4, 4, 0, 0]} name="Acres" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
