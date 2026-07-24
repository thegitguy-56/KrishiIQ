import axios from 'axios'

const API_URL = 'https://krishiiq-6su1.onrender.com'

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token =
    localStorage.getItem('access_token') ||
    localStorage.getItem('token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem('refresh_token')

      if (refresh && !error.config._retry) {
        error.config._retry = true

        try {
          const { data } = await axios.post(
            `${API_URL}/api/v1/auth/refresh`,
            null,
            {
              params: { refresh_token: refresh },
            }
          )

          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('token', data.access_token)

          error.config.headers.Authorization = `Bearer ${data.access_token}`

          return api.request(error.config)
        } catch {
          localStorage.clear()
          window.location.href = '/#/login'
        }
      } else {
        localStorage.clear()
        window.location.href = '/#/login'
      }
    }

    return Promise.reject(error)
  }
)

export const authApi = {
  login: (phone, password) =>
    api.post('/auth/login', { phone, password }),

  register: (data) =>
    api.post('/auth/register', data),
}

export const dashboardApi = {
  getOverview: (district) =>
    api.get('/dashboard/overview', {
      params: district ? { district } : {},
    }),

  getDistrictHeatmap: () =>
    api.get('/dashboard/district-heatmap'),

  getPestSpreadRisk: (district) =>
    api.get('/dashboard/pest-spread-risk', {
      params: { district },
    }),

  getWaterUsage: () =>
    api.get('/dashboard/water-usage'),

  getFarmers: (district) =>
    api.get('/dashboard/farmers', {
      params: district ? { district } : {},
    }),

  getFarmsMap: (district) =>
    api.get('/dashboard/farms-map', {
      params: district ? { district } : {},
    }),

  getCropDistribution: () =>
    api.get('/dashboard/crop-distribution'),

  getYieldTrends: () =>
    api.get('/dashboard/yield-trends'),

  getDistricts: () =>
    api.get('/dashboard/districts'),
}

export const aiApi = {
  getPublicConfig: () =>
    api.get('/ai/config/public'),

  chat: (message, history = []) =>
    api.post('/ai/chat', { message, history }),
}

export const farmApi = {
  list: () => api.get('/farms/'),
  create: (data) => api.post('/farms/', data),
  get: (id) => api.get(`/farms/${id}`),
  update: (id, data) => api.patch(`/farms/${id}`, data),
  delete: (id) => api.delete(`/farms/${id}`),
}

export const cropApi = {
  list: () => api.get('/crops/'),
  create: (data) => api.post('/crops/', data),
  update: (id, data) => api.patch(`/crops/${id}`, data),
}

export const sensorApi = {
  getLatest: (farmId) =>
    api.get(`/sensors/farm/${farmId}/latest`),

  getHistory: (farmId, hours = 24) =>
    api.get(`/sensors/farm/${farmId}/history`, {
      params: { hours },
    }),
}

export const diseaseApi = {
  getHistory: (farmId) =>
    api.get(`/disease/farm/${farmId}/history`),

  getDistrictAlerts: (district, severity = 'high') =>
    api.get(`/disease/alerts/district/${district}`, {
      params: { severity },
    }),

  detect: (formData) =>
    api.post('/disease/detect', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
}

export const advisoryApi = {
  getPersonalized: () =>
    api.get('/advisory/personalized'),

  markRead: (id) =>
    api.patch(`/advisory/${id}/read`),
}

export const weatherApi = {
  getForecast: (lat, lon) =>
    api.get('/weather/forecast', {
      params: { lat, lon },
    }),
}

export default api