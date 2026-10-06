import { useAuth } from '@/contexts/AuthContext'

export const useCompany = () => {
  const { activeCompany, activeCompanyId, companies, setActiveCompanyId } = useAuth()

  return {
    activeCompany,
    activeCompanyId,
    companies,
    switchCompany: setActiveCompanyId,
    hasCompany: !!activeCompanyId && companies.length > 0,
  }
}
