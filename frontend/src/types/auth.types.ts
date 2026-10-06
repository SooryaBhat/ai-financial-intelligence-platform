// Auth type definitions — mirrors backend app/schemas/auth.py

export interface LoginRequest {
  email: string
  password: string
}

export interface SignupRequest {
  email: string
  password: string
  full_name: string
  phone?: string
}

export interface OnboardRequest {
  company_name: string
  company_slug: string
  industry?: string
  country?: string
  currency: string
  timezone: string
}

export interface TokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in?: number
}

export interface AuthUser {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  phone?: string
  is_active: boolean
}

export interface CompanyMembership {
  id?: string
  company_id: string
  name?: string
  company_name: string
  company_slug: string
  role?: string
  role_name?: string
  is_owner?: boolean
}

export interface MeResponse {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  is_active?: boolean
  companies?: CompanyMembership[]
}

export interface AuthState {
  user: MeResponse | null
  accessToken: string | null
  refreshToken: string | null
  activeCompanyId: string | null
  isAuthenticated: boolean
  isLoading: boolean
}
