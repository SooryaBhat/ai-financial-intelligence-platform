import React, { useState, useRef, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Menu,
  Bell,
  Search as SearchIcon,
  Bot,
  HelpCircle,
  Building2,
  ChevronDown,
  LayoutGrid,
  TrendingUp,
  Package,
  ShoppingCart,
  Receipt,
  Users,
  Briefcase,
  Layers,
  FileText,
  Warehouse,
  BrainCircuit,
} from 'lucide-react'
import { AlladinLogo } from '@/components/brand/AlladinLogo'
import { ProfileMenu } from './ProfileMenu'
import { useAuth } from '@/hooks/useAuth'
import { useQuery } from '@tanstack/react-query'
import { notificationService } from '@/services/erp.service'
import { cn } from '@/lib/utils'

export interface NavbarProps {
  onMobileMenuToggle: () => void
  isSidebarCollapsed: boolean
  onOpenSearch: () => void
  onToggleAIAssistant: () => void
}

export const Navbar: React.FC<NavbarProps> = ({
  onMobileMenuToggle,
  isSidebarCollapsed: _isSidebarCollapsed,
  onOpenSearch,
  onToggleAIAssistant,
}) => {
  const location = useLocation()
  const { activeCompany, companies, setActiveCompanyId } = useAuth()

  const [isErpMenuOpen, setIsErpMenuOpen] = useState(false)
  const [isForecastMenuOpen, setIsForecastMenuOpen] = useState(false)
  const [isCompanyMenuOpen, setIsCompanyMenuOpen] = useState(false)

  const erpRef = useRef<HTMLDivElement>(null)
  const forecastRef = useRef<HTMLDivElement>(null)
  const companyRef = useRef<HTMLDivElement>(null)

  // Fetch unread notification count
  const { data: unreadCount } = useQuery({
    queryKey: ['notifications-unread-count'],
    queryFn: () => notificationService.getUnreadCount(),
    refetchInterval: 60000,
  })

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (erpRef.current && !erpRef.current.contains(e.target as Node)) {
        setIsErpMenuOpen(false)
      }
      if (forecastRef.current && !forecastRef.current.contains(e.target as Node)) {
        setIsForecastMenuOpen(false)
      }
      if (companyRef.current && !companyRef.current.contains(e.target as Node)) {
        setIsCompanyMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Close menus on route change
  useEffect(() => {
    setIsErpMenuOpen(false)
    setIsForecastMenuOpen(false)
    setIsCompanyMenuOpen(false)
  }, [location.pathname])

  const isErpActive =
    !location.pathname.startsWith('/ml') &&
    !location.pathname.startsWith('/help') &&
    location.pathname !== '/'

  const isForecastActive = location.pathname.startsWith('/ml')
  const isHelpActive = location.pathname.startsWith('/help')

  return (
    <header className="sticky top-0 z-30 h-14 bg-white border-b border-slate-200 transition-colors flex items-center justify-between px-3 sm:px-5 select-none">
      {/* ── Left section: Brand, Mobile Toggle, Primary Destinations ── */}
      <div className="flex items-center gap-2 sm:gap-4">
        <button
          onClick={onMobileMenuToggle}
          className="lg:hidden p-1.5 rounded-md text-slate-600 hover:bg-slate-100 transition-colors"
          title="Toggle Navigation Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* ALLADIN Logo on top bar */}
        <AlladinLogo size="sm" showFullName={false} to="/dashboard" />

        <div className="h-4 w-px bg-slate-200 hidden md:block" />

        {/* ── Primary Destinations Tabs (Odoo-inspired) ── */}
        <nav className="hidden md:flex items-center gap-1 text-xs">
          {/* 1. ERP Tab & App Launcher Dropdown */}
          <div className="relative" ref={erpRef}>
            <button
              onClick={() => setIsErpMenuOpen(!isErpMenuOpen)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md font-semibold transition-colors',
                isErpActive
                  ? 'bg-teal-50 text-teal-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              )}
            >
              <LayoutGrid className="w-3.5 h-3.5 text-teal-700" />
              <span>ERP</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {/* Odoo-style ERP Modules Grid Dropdown */}
            {isErpMenuOpen && (
              <div className="absolute left-0 mt-1.5 w-80 bg-white border border-slate-200 rounded-xl shadow-xl py-3 px-3 z-50 animate-fade-in">
                <div className="px-2 pb-2 mb-2 border-b border-slate-100 flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    ALLADIN ERP Suite
                  </span>
                  <Link
                    to="/dashboard"
                    onClick={() => setIsErpMenuOpen(false)}
                    className="text-[10px] font-semibold text-teal-700 hover:underline"
                  >
                    Dashboard &rarr;
                  </Link>
                </div>

                <div className="grid grid-cols-2 gap-1 text-xs">
                  <Link
                    to="/sales"
                    onClick={() => setIsErpMenuOpen(false)}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 text-slate-700 hover:text-teal-800 transition-colors"
                  >
                    <ShoppingCart className="w-4 h-4 text-teal-600" />
                    <span>Sales Orders</span>
                  </Link>

                  <Link
                    to="/invoices"
                    onClick={() => setIsErpMenuOpen(false)}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 text-slate-700 hover:text-teal-800 transition-colors"
                  >
                    <Receipt className="w-4 h-4 text-teal-600" />
                    <span>Invoices</span>
                  </Link>

                  <Link
                    to="/products"
                    onClick={() => setIsErpMenuOpen(false)}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 text-slate-700 hover:text-teal-800 transition-colors"
                  >
                    <Package className="w-4 h-4 text-teal-600" />
                    <span>Products</span>
                  </Link>

                  <Link
                    to="/inventory"
                    onClick={() => setIsErpMenuOpen(false)}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 text-slate-700 hover:text-teal-800 transition-colors"
                  >
                    <Warehouse className="w-4 h-4 text-teal-600" />
                    <span>Inventory</span>
                  </Link>

                  <Link
                    to="/purchases"
                    onClick={() => setIsErpMenuOpen(false)}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 text-slate-700 hover:text-teal-800 transition-colors"
                  >
                    <Briefcase className="w-4 h-4 text-teal-600" />
                    <span>Purchases</span>
                  </Link>

                  <Link
                    to="/customers"
                    onClick={() => setIsErpMenuOpen(false)}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 text-slate-700 hover:text-teal-800 transition-colors"
                  >
                    <Users className="w-4 h-4 text-teal-600" />
                    <span>Customers</span>
                  </Link>

                  <Link
                    to="/expenses"
                    onClick={() => setIsErpMenuOpen(false)}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 text-slate-700 hover:text-teal-800 transition-colors"
                  >
                    <Layers className="w-4 h-4 text-teal-600" />
                    <span>Expenses</span>
                  </Link>

                  <Link
                    to="/reports"
                    onClick={() => setIsErpMenuOpen(false)}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 text-slate-700 hover:text-teal-800 transition-colors"
                  >
                    <FileText className="w-4 h-4 text-teal-600" />
                    <span>Reports</span>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* 2. Forecasting Tab & Dropdown */}
          <div className="relative" ref={forecastRef}>
            <button
              onClick={() => setIsForecastMenuOpen(!isForecastMenuOpen)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md font-semibold transition-colors',
                isForecastActive
                  ? 'bg-teal-50 text-teal-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              )}
            >
              <TrendingUp className="w-3.5 h-3.5 text-teal-700" />
              <span>Forecasting</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {isForecastMenuOpen && (
              <div className="absolute left-0 mt-1.5 w-64 bg-white border border-slate-200 rounded-xl shadow-xl py-2 z-50 animate-fade-in text-xs">
                <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100">
                  ML Prediction Engines
                </div>
                <div className="py-1">
                  <Link
                    to="/ml/revenue"
                    onClick={() => setIsForecastMenuOpen(false)}
                    className="flex items-center gap-2 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <TrendingUp className="w-3.5 h-3.5 text-teal-600" />
                    <span>Revenue Forecast</span>
                  </Link>
                  <Link
                    to="/ml/sales"
                    onClick={() => setIsForecastMenuOpen(false)}
                    className="flex items-center gap-2 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ShoppingCart className="w-3.5 h-3.5 text-teal-600" />
                    <span>Sales Demand Forecast</span>
                  </Link>
                  <Link
                    to="/ml/inventory"
                    onClick={() => setIsForecastMenuOpen(false)}
                    className="flex items-center gap-2 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <Package className="w-3.5 h-3.5 text-teal-600" />
                    <span>Inventory Reorder Demand</span>
                  </Link>
                  <Link
                    to="/ml/profit"
                    onClick={() => setIsForecastMenuOpen(false)}
                    className="flex items-center gap-2 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <TrendingUp className="w-3.5 h-3.5 text-teal-600" />
                    <span>Profit Margin Prediction</span>
                  </Link>
                  <Link
                    to="/ml/expense"
                    onClick={() => setIsForecastMenuOpen(false)}
                    className="flex items-center gap-2 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <Layers className="w-3.5 h-3.5 text-teal-600" />
                    <span>Expense Forecast</span>
                  </Link>
                  <Link
                    to="/ml/business-health"
                    onClick={() => setIsForecastMenuOpen(false)}
                    className="flex items-center gap-2 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <BrainCircuit className="w-3.5 h-3.5 text-teal-600" />
                    <span>Business Health Score</span>
                  </Link>
                  <Link
                    to="/ml/anomalies"
                    onClick={() => setIsForecastMenuOpen(false)}
                    className="flex items-center gap-2 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <BrainCircuit className="w-3.5 h-3.5 text-teal-600" />
                    <span>Anomaly Detection</span>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* 3. AI Assistant Trigger */}
          <button
            onClick={onToggleAIAssistant}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-slate-700 hover:text-teal-800 hover:bg-teal-50 transition-colors font-semibold"
          >
            <Bot className="w-3.5 h-3.5 text-teal-700" />
            <span>AI Assistant</span>
          </button>

          {/* 4. Help & Docs */}
          <Link
            to="/help"
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-md font-semibold transition-colors',
              isHelpActive
                ? 'bg-teal-50 text-teal-800'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            )}
          >
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
            <span>Help</span>
          </Link>
        </nav>
      </div>

      {/* ── Right section: Global Search, Active Company, Notifications, Profile ── */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Global Search Button */}
        <button
          onClick={onOpenSearch}
          className="flex items-center gap-2 px-2.5 sm:px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-xs text-slate-500 hover:border-slate-300 hover:bg-white hover:text-slate-700 transition-all shadow-2xs"
          title="Search commands and records (Ctrl+K)"
        >
          <SearchIcon className="w-3.5 h-3.5 text-slate-400" />
          <span className="hidden sm:inline">Search records or modules...</span>
          <kbd className="hidden sm:inline-block ml-2 px-1.5 py-0.5 text-[10px] font-mono rounded bg-slate-200 text-slate-600 border border-slate-300">
            ⌘K
          </kbd>
        </button>

        {/* Company / Workspace Switcher Dropdown */}
        <div className="relative hidden md:block" ref={companyRef}>
          <button
            onClick={() => setIsCompanyMenuOpen(!isCompanyMenuOpen)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-800 transition-colors"
            title="Active Organization Workspace"
          >
            <Building2 className="w-3.5 h-3.5 text-teal-700 shrink-0" />
            <span className="max-w-[130px] truncate">
              {activeCompany?.company_name || 'Organization'}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {isCompanyMenuOpen && (
            <div className="absolute right-0 mt-1.5 w-56 bg-white border border-slate-200 rounded-xl shadow-xl py-2 z-50 text-xs animate-fade-in">
              <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100">
                Switch Organization
              </div>
              <div className="py-1 max-h-48 overflow-y-auto">
                {companies.map((c) => {
                  const compId = c.company_id || c.id || ''
                  const isCurrent = (activeCompany?.company_id || activeCompany?.id) === compId
                  return (
                    <button
                      key={compId}
                      onClick={() => {
                        setActiveCompanyId(compId)
                        setIsCompanyMenuOpen(false)
                      }}
                      className={cn(
                        'w-full text-left px-3 py-2 flex items-center justify-between transition-colors',
                        isCurrent
                          ? 'bg-teal-50 text-teal-800 font-semibold'
                          : 'text-slate-700 hover:bg-slate-50'
                      )}
                    >
                      <span className="truncate">{c.company_name}</span>
                      {isCurrent && <span className="w-1.5 h-1.5 rounded-full bg-teal-600" />}
                    </button>
                  )
                })}
              </div>
              <div className="pt-1 border-t border-slate-100 px-2">
                <Link
                  to="/onboard"
                  onClick={() => setIsCompanyMenuOpen(false)}
                  className="block w-full py-1.5 text-center text-[11px] font-semibold text-teal-700 hover:bg-teal-50 rounded"
                >
                  + Add New Company
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Notifications Icon Button */}
        <Link
          to="/notifications"
          className="relative p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          title="Notifications & Alerts"
        >
          <Bell className="w-4 h-4" />
          {typeof unreadCount === 'number' && unreadCount > 0 && (
            <span className="absolute top-1 right-1 flex items-center justify-center min-w-4 h-4 px-1 rounded-full bg-teal-600 text-white text-[9px] font-bold">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Link>

        {/* User Profile Menu */}
        <div className="pl-1 border-l border-slate-200">
          <ProfileMenu />
        </div>
      </div>
    </header>
  )
}
