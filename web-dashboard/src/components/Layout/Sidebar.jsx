import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Users, Map, AlertTriangle, BarChart3, Leaf, LogOut } from 'lucide-react'
import useAuthStore from '../../store/authStore'
import { useNavigate } from 'react-router-dom'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/farmers', icon: Users, label: 'Farmers' },
  { to: '/map', icon: Map, label: 'Farm Map' },
  { to: '/disease-alerts', icon: AlertTriangle, label: 'Disease Alerts' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
]

export default function Sidebar() {
  const { logout, user } = useAuthStore()
  const navigate = useNavigate()

  return (
    <aside className="w-64 bg-brand-900 text-white flex flex-col">
      <div className="p-6 flex items-center gap-3 border-b border-brand-700">
        <Leaf className="w-8 h-8 text-brand-400" />
        <div>
          <div className="font-bold text-lg leading-tight">KrishiIQ</div>
          <div className="text-xs text-brand-400">Agriculture Intelligence</div>
        </div>
      </div>
      <nav className="flex-1 py-4 px-3 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand-600 text-white'
                  : 'text-brand-200 hover:bg-brand-800 hover:text-white'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-brand-700 space-y-2">
        <div className="text-xs text-brand-300 px-2">
          Signed in as <span className="font-semibold text-white capitalize">{user?.role || 'officer'}</span>
        </div>
        <button
          onClick={() => { logout(); navigate('/login') }}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-brand-200 hover:bg-brand-800"
        >
          <LogOut className="w-4 h-4" /> Sign Out
        </button>
      </div>
    </aside>
  )
}
