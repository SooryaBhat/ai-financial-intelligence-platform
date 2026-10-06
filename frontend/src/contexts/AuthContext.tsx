import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authService } from '@/services/auth.service'
import {
  MeResponse,
  CompanyMembership,
  LoginRequest,
  SignupRequest,
} from '@/types/auth.types'

interface AuthContextType {
  user: MeResponse | null
  isAuthenticated: boolean
  isLoading: boolean
  activeCompanyId: string | null
  activeCompany: CompanyMembership | null
  companies: CompanyMembership[]
  setActiveCompanyId: (id: string) => void
  login: (credentials: LoginRequest) => Promise<void>
  signup: (data: SignupRequest) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<MeResponse | null>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<MeResponse | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [activeCompanyId, setActiveCompanyIdState] = useState<string | null>(() => {
    return localStorage.getItem('active_company_id')
  })

  const setActiveCompanyId = useCallback((id: string) => {
    localStorage.setItem('active_company_id', id)
    setActiveCompanyIdState(id)
  }, [])

  const refreshUser = useCallback(async (): Promise<MeResponse | null> => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return null
    }

    try {
      const userData = await authService.getMe()
      setUser(userData)

      // Automatically set active company if not set or invalid
      if (userData.companies && userData.companies.length > 0) {
        const storedCompanyId = localStorage.getItem('active_company_id')
        const isValidStored = storedCompanyId && userData.companies.some((c) => (c.company_id || c.id) === storedCompanyId)
        if (!isValidStored) {
          const defaultCompany = userData.companies[0]
          const compId = defaultCompany.company_id || defaultCompany.id
          if (compId) {
            setActiveCompanyId(compId)
          }
        }
      }

      return userData
    } catch {
      setUser(null)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('active_company_id')
      return null
    } finally {
      setIsLoading(false)
    }
  }, [setActiveCompanyId])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true)
    try {
      const tokenData = await authService.login(credentials)
      if (tokenData.access_token) {
        localStorage.setItem('access_token', tokenData.access_token)
        if (tokenData.refresh_token) {
          localStorage.setItem('refresh_token', tokenData.refresh_token)
        }
        await refreshUser()
      }
    } finally {
      setIsLoading(false)
    }
  }

  const signup = async (data: SignupRequest) => {
    setIsLoading(true)
    try {
      const tokenData = await authService.signup(data)
      if (tokenData.access_token) {
        localStorage.setItem('access_token', tokenData.access_token)
        if (tokenData.refresh_token) {
          localStorage.setItem('refresh_token', tokenData.refresh_token)
        }
        await refreshUser()
      }
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    setIsLoading(true)
    try {
      await authService.logout()
    } finally {
      setUser(null)
      setActiveCompanyIdState(null)
      setIsLoading(false)
    }
  }

  const activeCompany =
    user?.companies?.find((c) => (c.company_id || c.id) === activeCompanyId) ||
    user?.companies?.[0] ||
    (activeCompanyId ? ({ company_id: activeCompanyId, id: activeCompanyId, company_name: 'Active Company' } as any) : null)

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        activeCompanyId,
        activeCompany,
        companies: user?.companies || [],
        setActiveCompanyId,
        login,
        signup,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
