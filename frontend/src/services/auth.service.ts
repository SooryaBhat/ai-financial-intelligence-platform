import api from '@/lib/api'
import {
  LoginRequest,
  SignupRequest,
  OnboardRequest,
  TokenResponse,
  MeResponse,
  CompanyMembership,
} from '@/types/auth.types'
import { ApiSuccessResponse, ApiMessageResponse } from '@/types/api.types'

export const authService = {
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await api.post<ApiSuccessResponse<TokenResponse>>('/api/v1/auth/login', credentials)
    return response.data.data
  },

  async signup(data: SignupRequest): Promise<TokenResponse> {
    const response = await api.post<ApiSuccessResponse<TokenResponse>>('/api/v1/auth/signup', data)
    return response.data.data
  },

  async logout(): Promise<void> {
    try {
      await api.post<ApiMessageResponse>('/api/v1/auth/logout')
    } catch {
      // Ignore errors on logout
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('active_company_id')
    }
  },

  async getMe(): Promise<MeResponse> {
    const response = await api.get<ApiSuccessResponse<MeResponse>>('/api/v1/auth/me')
    return response.data.data
  },

  async onboard(data: OnboardRequest): Promise<CompanyMembership> {
    const response = await api.post<ApiSuccessResponse<CompanyMembership>>('/api/v1/auth/onboard', data)
    return response.data.data
  },

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await api.post<ApiSuccessResponse<TokenResponse>>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data.data
  },
}
