import { create } from 'zustand'
import { authApi } from '../services/api'

const useAuthStore = create((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  role: localStorage.getItem('role'),
  isAuthenticated: !!localStorage.getItem('access_token'),

  login: async (phone, password) => {
    const response = await authApi.login(phone, password)
    const data = response.data

    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('role', data.role)
    localStorage.setItem('user_id', data.user_id)
    localStorage.setItem('preferred_language', data.preferred_language || 'en')

    set({
      token: data.access_token,
      role: data.role,
      isAuthenticated: true,
      user: {
        id: data.user_id,
        role: data.role,
        preferred_language: data.preferred_language || 'en',
      },
    })

    return data
  },

  logout: () => {
    localStorage.clear()
    set({
      user: null,
      token: null,
      role: null,
      isAuthenticated: false,
    })
  },
}))

export default useAuthStore