import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Leaf, Smartphone } from 'lucide-react'
import toast from 'react-hot-toast'
import useAuthStore from '../store/authStore'

export default function Login() {
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const data = await login(phone, password)
      if (data.role === 'farmer') {
        useAuthStore.getState().logout()
        toast.error('Farmers must use the KrishiIQ mobile app')
        navigate('/unauthorized')
        return
      }
      if (!['officer', 'admin'].includes(data.role)) {
        toast.error('Unknown role')
        return
      }
      toast.success(`Welcome, ${data.role === 'admin' ? 'Administrator' : 'Officer'}`)
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-brand-700 to-brand-500 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-brand-600 rounded-xl flex items-center justify-center">
            <Leaf className="w-7 h-7 text-white" />
          </div>
          <div>
            <div className="font-bold text-2xl text-gray-900">KrishiIQ</div>
            <div className="text-sm text-gray-500">Officer & Admin Portal</div>
          </div>
        </div>

        <div className="bg-brand-50 border border-brand-100 rounded-lg p-3 mb-6 flex gap-2 text-sm text-brand-800">
          <Smartphone className="w-5 h-5 shrink-0" />
          <span>Farmers: use the mobile app. This portal is for officers and admins only.</span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="9000000001"
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <button type="submit" disabled={loading} className="w-full btn-primary py-3 text-base">
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-gray-400">
          Demo: Officer 9000000001 / officer123 · Admin 9000000003 / admin123
        </p>
      </div>
    </div>
  )
}
