import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Spinner } from '@/components/ui/Spinner'

export interface ProtectedRouteProps {
  children: React.ReactNode
  requireOnboarding?: boolean
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireOnboarding = true,
}) => {
  const { isAuthenticated, isLoading, activeCompany, activeCompanyId, user } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-50 dark:bg-surface-950">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Check whether user has an active company or company membership
  const hasCompany = (user?.companies && user.companies.length > 0) || !!activeCompany || !!activeCompanyId
  if (requireOnboarding && !hasCompany) {
    if (location.pathname !== '/onboard') {
      return <Navigate to="/onboard" replace />
    }
  }

  return <>{children}</>
}
