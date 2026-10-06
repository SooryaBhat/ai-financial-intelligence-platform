import React from 'react'
import { Menu, Bell, Search as SearchIcon } from 'lucide-react'
import { Breadcrumbs } from './Breadcrumbs'
import { ThemeSwitch } from './ThemeSwitch'
import { ProfileMenu } from './ProfileMenu'
import { cn } from '@/lib/utils'

export interface NavbarProps {
  onMobileMenuToggle: () => void
  isSidebarCollapsed: boolean
}

export const Navbar: React.FC<NavbarProps> = ({ onMobileMenuToggle, isSidebarCollapsed }) => {
  return (
    <header
      className={cn(
        'sticky top-0 z-20 h-[60px] bg-white/80 dark:bg-surface-900/80 backdrop-blur-md border-b border-surface-200 dark:border-surface-800 transition-all duration-300 flex items-center justify-between px-4 sm:px-6'
      )}
    >
      {/* Left section: Mobile Hamburger & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMobileMenuToggle}
          className="lg:hidden p-2 rounded-lg text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="hidden sm:block">
          <Breadcrumbs />
        </div>
      </div>

      {/* Right section: Global Search, Notifications, Theme, Profile */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Search button trigger */}
        <button
          onClick={() => alert('Search dialog opened')}
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-800/60 text-xs text-surface-400 hover:border-surface-300 dark:hover:border-surface-700 transition-colors"
        >
          <SearchIcon className="w-3.5 h-3.5" />
          <span>Search records or commands...</span>
          <kbd className="ml-4 px-1.5 py-0.5 text-[10px] font-mono rounded bg-surface-200 dark:bg-surface-700 text-surface-600 dark:text-surface-300">
            ⌘K
          </kbd>
        </button>

        {/* Notifications */}
        <button
          onClick={() => alert('No new notifications')}
          className="relative p-2 rounded-lg text-surface-500 hover:text-surface-900 dark:text-surface-400 dark:hover:text-surface-100 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-primary-600 animate-pulse" />
        </button>

        {/* Theme Switch */}
        <ThemeSwitch />

        {/* Profile Menu */}
        <div className="pl-1 sm:pl-2 border-l border-surface-200 dark:border-surface-800">
          <ProfileMenu />
        </div>
      </div>
    </header>
  )
}
