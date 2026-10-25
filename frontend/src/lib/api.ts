import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

export const PRODUCTION_API_URL = 'https://ai-financial-intelligence-platform-89re.onrender.com'
export const LOCAL_DEV_API_URL = 'http://localhost:8000'

/**
 * Resolves the API base URL:
 * 1. Prioritizes VITE_API_BASE_URL, with fallback to legacy VITE_API_URL.
 * 2. Trims whitespace and trailing slashes.
 * 3. Strips trailing '/api/v1' or '/api' suffixes to prevent duplicated API prefixes.
 * 4. In production mode (import.meta.env.PROD), never silently falls back to localhost:
 *    if the resolved URL is empty or points to localhost/127.0.0.1, it defaults to PRODUCTION_API_URL.
 * 5. In local development (import.meta.env.DEV), preserves localhost:8000.
 */
export function resolveApiBaseUrl(
  envBaseUrl?: string,
  envLegacyUrl?: string,
  isProd: boolean = import.meta.env.PROD
): string {
  const raw = (envBaseUrl || envLegacyUrl || '').trim()

  if (raw) {
    let sanitized = raw.replace(/\/+$/, '')
    sanitized = sanitized.replace(/\/api\/v1$/, '').replace(/\/api$/, '')

    if (isProd) {
      const isLocal = /^(https?:\/\/)?(localhost|127\.0\.0\.1)(:\d+)?/i.test(sanitized)
      if (isLocal) {
        return PRODUCTION_API_URL
      }
    }
    return sanitized
  }

  return isProd ? PRODUCTION_API_URL : LOCAL_DEV_API_URL
}

export const API_BASE_URL = resolveApiBaseUrl(
  import.meta.env.VITE_API_BASE_URL,
  import.meta.env.VITE_API_URL
)

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request Interceptor: Attach JWT & X-Company-ID
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    const companyId = localStorage.getItem('active_company_id')
    if (companyId) {
      config.headers['X-Company-ID'] = companyId
    }

    const branchId = localStorage.getItem('active_branch_id')
    if (branchId) {
      config.headers['X-Branch-ID'] = branchId
    }

    return config
  },
  (error) => Promise.reject(error)
)

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}> = []

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Response Interceptor: Handle 401 & Refresh Token
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Check if error is 401 Unauthorized and not already retrying
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      // Avoid infinite refresh loops if refresh endpoint itself failed
      if (originalRequest.url?.includes('/auth/refresh') || originalRequest.url?.includes('/auth/login')) {
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            return api(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        isRefreshing = false
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('active_company_id')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        const { data } = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const newAccessToken = data.data?.access_token || data.access_token
        const newRefreshToken = data.data?.refresh_token || data.refresh_token || refreshToken

        if (newAccessToken) {
          localStorage.setItem('access_token', newAccessToken)
          if (newRefreshToken) {
            localStorage.setItem('refresh_token', newRefreshToken)
          }

          api.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          }

          processQueue(null, newAccessToken)
          return api(originalRequest)
        } else {
          throw new Error('Refresh token failed')
        }
      } catch (refreshErr) {
        processQueue(refreshErr as Error, null)
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('active_company_id')
        window.location.href = '/login'
        return Promise.reject(refreshErr)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default api
