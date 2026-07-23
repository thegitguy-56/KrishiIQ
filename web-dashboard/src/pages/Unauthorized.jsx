import { Link } from 'react-router-dom'
import { ShieldAlert } from 'lucide-react'
import useAuthStore from '../store/authStore'

export default function Unauthorized() {
  const { logout, user } = useAuthStore()

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl shadow-lg max-w-md w-full p-8 text-center">
        <ShieldAlert className="w-14 h-14 text-amber-500 mx-auto mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">Access Restricted</h1>
        <p className="text-gray-600 text-sm mb-6">
          {user?.role === 'farmer'
            ? 'Farmer accounts must use the KrishiIQ mobile app. This portal is for agriculture officers and administrators.'
            : 'You do not have permission to view this page.'}
        </p>
        <div className="flex flex-col gap-2">
          <button onClick={logout} className="btn-primary w-full">
            Sign Out
          </button>
          <Link to="/login" className="text-sm text-brand-600 hover:underline">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  )
}
