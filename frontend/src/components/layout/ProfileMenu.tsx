import React, { useState, useRef, useEffect } from 'react'
import { LogOut, User, Building, Settings, ChevronDown } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { useToast } from '@/hooks/useToast'

export const ProfileMenu: React.FC = () => {
  const { user, logout, activeCompany } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const toast = useToast()

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = async () => {
    try {
      await logout()
      toast.success('Logged out successfully')
      navigate('/login')
    } catch {
      toast.error('Logout failed')
    }
  }

  const userInitial = user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email?.charAt(0).toUpperCase() || 'U'

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
      >
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-600 text-white font-semibold text-xs shadow-sm">
          {userInitial}
        </div>
        <div className="hidden md:flex flex-col text-left">
          <span className="text-xs font-semibold text-surface-900 dark:text-surface-100 max-w-[120px] truncate">
            {user?.full_name || 'User'}
          </span>
          <span className="text-[10px] text-surface-500 dark:text-surface-400 max-w-[120px] truncate">
            {user?.email}
          </span>
        </div>
        <ChevronDown className="w-4 h-4 text-surface-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 rounded-xl shadow-card-lg py-1.5 z-50 text-xs">
          <div className="px-4 py-2 border-b border-surface-100 dark:border-surface-800">
            <p className="font-semibold text-surface-900 dark:text-surface-100">{user?.full_name}</p>
            <p className="text-surface-500 dark:text-surface-400 truncate">{user?.email}</p>
            {activeCompany && (
              <div className="mt-1.5 pt-1.5 border-t border-surface-100 dark:border-surface-800/60 flex items-center gap-1.5 text-primary-600 dark:text-primary-400 font-medium">
                <Building className="w-3.5 h-3.5" />
                <span className="truncate">{activeCompany.company_name}</span>
              </div>
            )}
          </div>

          <div className="py-1">
            <button
              onClick={() => {
                setIsOpen(false)
                navigate('/dashboard')
              }}
              className="w-full px-4 py-2 flex items-center gap-2 text-surface-700 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
            >
              <User className="w-4 h-4 text-surface-400" />
              <span>Dashboard</span>
            </button>
            <button
              onClick={() => {
                setIsOpen(false)
                navigate('/onboard')
              }}
              className="w-full px-4 py-2 flex items-center gap-2 text-surface-700 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
            >
              <Settings className="w-4 h-4 text-surface-400" />
              <span>Company Setup</span>
            </button>
          </div>

          <div className="border-t border-surface-100 dark:border-surface-800 pt-1">
            <button
              onClick={handleLogout}
              className="w-full px-4 py-2 flex items-center gap-2 text-danger-600 hover:bg-danger-50 dark:hover:bg-danger-950/30 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
