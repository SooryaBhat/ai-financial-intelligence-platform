import React, { useState, useRef, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Bell,
  Search as SearchIcon,
  HelpCircle,
  Building2,
  ChevronDown,
  LayoutGrid,
  TrendingUp,
  Package,
  ShoppingCart,
  DollarSign,
  Settings,
  GitBranch,
  Menu,
  X,
} from 'lucide-react'
import { AlladinLogo } from '@/components/brand/AlladinLogo'
import { ModuleIcon } from '@/components/ui/ModuleIcon'
import { ProfileMenu } from './ProfileMenu'
import { useAuth } from '@/hooks/useAuth'
import { useQuery } from '@tanstack/react-query'
import { notificationService, branchService } from '@/services/erp.service'
import { cn } from '@/lib/utils'

export interface NavbarProps {
  onMobileMenuToggle?: () => void
  isSidebarCollapsed?: boolean
  onOpenSearch: () => void
  onToggleAIAssistant: () => void
}

type DropdownKey = 'commercial' | 'inventory' | 'finance' | 'ml' | 'admin' | null

export const Navbar: React.FC<NavbarProps> = ({
  onOpenSearch,
  onToggleAIAssistant,
}) => {
  const location = useLocation()
  const { isAuthenticated, activeCompany, companies, setActiveCompanyId, activeBranchId, setActiveBranchId } = useAuth()

  const [activeDropdown, setActiveDropdown] = useState<DropdownKey>(null)
  const [isCompanyMenuOpen, setIsCompanyMenuOpen] = useState(false)
  const [isBranchMenuOpen, setIsBranchMenuOpen] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [mobileSearch, setMobileSearch] = useState('')

  const navRef = useRef<HTMLDivElement>(null)
  const companyRef = useRef<HTMLDivElement>(null)
  const branchRef = useRef<HTMLDivElement>(null)

  // Fetch unread notification count — scoped to authenticated session and company
  const companyKey = activeCompany?.company_id || activeCompany?.id
  const { data: unreadCount, isError: isUnreadCountError } = useQuery({
    queryKey: ['notifications-unread-count', companyKey],
    queryFn: () => notificationService.getUnreadCount(),
    enabled: Boolean(isAuthenticated && companyKey),
    refetchInterval: 60000,
    retry: (failureCount, error: any) => {
      // Do not endlessly retry on 401/403/404
      const status = error?.response?.status
      if (status === 401 || status === 403 || status === 404) {
        return false
      }
      return failureCount < 2
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
    refetchOnWindowFocus: false,
  })

  // Fetch branches for active company
  const { data: branchesData } = useQuery({
    queryKey: ['navbar-branches', activeCompany?.id || activeCompany?.company_id],
    queryFn: () => branchService.list({ page_size: 50 }),
    enabled: !!(activeCompany?.id || activeCompany?.company_id),
  })
  const branches = branchesData?.items || []
  const activeBranch = branches.find((b: any) => b.id === activeBranchId)

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setActiveDropdown(null)
      }
      if (companyRef.current && !companyRef.current.contains(e.target as Node)) {
        setIsCompanyMenuOpen(false)
      }
      if (branchRef.current && !branchRef.current.contains(e.target as Node)) {
        setIsBranchMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Close menus on route change
  useEffect(() => {
    setActiveDropdown(null)
    setIsCompanyMenuOpen(false)
    setIsMobileMenuOpen(false)
  }, [location.pathname])

  const toggleDropdown = (key: DropdownKey) => {
    setActiveDropdown(activeDropdown === key ? null : key)
  }

  // Active section highlights
  const isCommercialActive = ['/sales', '/invoices', '/customers', '/payments'].some((p) =>
    location.pathname.startsWith(p)
  )
  const isInventoryActive = [
    '/products',
    '/inventory',
    '/stock-movements',
    '/warehouses',
    '/categories',
    '/purchases',
    '/suppliers',
  ].some((p) => location.pathname.startsWith(p))
  const isFinanceActive = ['/dashboard', '/expenses', '/reports'].some((p) =>
    location.pathname.startsWith(p)
  )
  const isMlActive = location.pathname.startsWith('/ml')
  const isAdminActive = ['/companies', '/branches', '/users', '/settings', '/notifications'].some((p) =>
    location.pathname.startsWith(p)
  )

  const isLauncherActive = location.pathname === '/apps'

  return (
    <header className="sticky top-0 z-30 h-14 bg-white border-b border-slate-200 transition-colors flex items-center justify-between px-3 sm:px-5 select-none shadow-xs w-full max-w-full">
      {/* ── Left section: Odoo App Launcher Button, Brand Logo, Modular Top Nav ── */}
      <div className="flex items-center gap-1.5 sm:gap-3 min-w-0" ref={navRef}>
        {/* Mobile Menu Toggle Button */}
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="lg:hidden p-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors shrink-0"
          title="Toggle Navigation Menu"
        >
          {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Odoo-style App Launcher Waffle Button */}
        <Link
          to="/apps"
          className={cn(
            'flex items-center gap-1.5 p-1.5 sm:px-2.5 sm:py-1.5 rounded-lg transition-all duration-150 shrink-0',
            isLauncherActive
              ? 'bg-teal-50 text-teal-800 ring-1 ring-teal-200'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          )}
          title="Application Launcher (Home)"
        >
          <LayoutGrid className="w-4 h-4 text-teal-700" />
          <span className="text-xs font-bold hidden sm:inline">Apps</span>
        </Link>

        {/* ALLADIN Logo */}
        <div className="shrink-0">
          <AlladinLogo size="sm" showFullName={false} to="/apps" />
        </div>

        <div className="h-4 w-px bg-slate-200 hidden lg:block shrink-0" />

        {/* ── Primary Modular Dropdowns (Odoo enterprise pattern) ── */}
        <nav className="hidden lg:flex items-center gap-0.5 xl:gap-1 text-xs shrink min-w-0">
          {/* 1. Commercial & Sales */}
          <div className="relative">
            <button
              onClick={() => toggleDropdown('commercial')}
              className={cn(
                'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md font-semibold transition-colors',
                isCommercialActive
                  ? 'bg-teal-50 text-teal-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              )}
            >
              <ShoppingCart className="w-3.5 h-3.5 text-teal-700" />
              <span>Sales</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {activeDropdown === 'commercial' && (
              <div className="absolute left-0 mt-1.5 w-60 bg-white border border-slate-200 rounded-xl shadow-xl py-2 z-50 animate-fade-in text-xs">
                <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100">
                  Sales & Commercial
                </div>
                <div className="py-1">
                  <Link
                    to="/sales"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="sales-orders" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Sales Orders</div>
                      <div className="text-[10px] text-slate-400">Order management & pipelines</div>
                    </div>
                  </Link>
                  <Link
                    to="/invoices"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="invoices-billing" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Invoices & Billing</div>
                      <div className="text-[10px] text-slate-400">Receivables & tax invoices</div>
                    </div>
                  </Link>
                  <Link
                    to="/customers"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="customers" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Customers Directory</div>
                      <div className="text-[10px] text-slate-400">Client CRM & account ledgers</div>
                    </div>
                  </Link>
                  <Link
                    to="/payments"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="payments" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Payments & Collections</div>
                      <div className="text-[10px] text-slate-400">Settlements & payment vouchers</div>
                    </div>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* 2. Procurement & Inventory */}
          <div className="relative">
            <button
              onClick={() => toggleDropdown('inventory')}
              className={cn(
                'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md font-semibold transition-colors',
                isInventoryActive
                  ? 'bg-teal-50 text-teal-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              )}
            >
              <Package className="w-3.5 h-3.5 text-teal-700" />
              <span>Inventory</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {activeDropdown === 'inventory' && (
              <div className="absolute left-0 mt-1.5 w-64 bg-white border border-slate-200 rounded-xl shadow-xl py-2 z-50 animate-fade-in text-xs">
                <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100">
                  Procurement & Inventory
                </div>
                <div className="py-1">
                  <Link
                    to="/products"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="products-skus" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Products & SKUs</div>
                      <div className="text-[10px] text-slate-400">Master catalog & pricing</div>
                    </div>
                  </Link>
                  <Link
                    to="/inventory"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="inventory" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Current Stock</div>
                      <div className="text-[10px] text-slate-400">On-hand quantities by location</div>
                    </div>
                  </Link>
                  <Link
                    to="/stock-movements"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="stock-movements" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Stock Movements</div>
                      <div className="text-[10px] text-slate-400">Inbound, outbound & transfers</div>
                    </div>
                  </Link>
                  <Link
                    to="/warehouses"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="warehouses" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Warehouses</div>
                      <div className="text-[10px] text-slate-400">Storage facilities & zones</div>
                    </div>
                  </Link>
                  <Link
                    to="/categories"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="categories" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Categories</div>
                      <div className="text-[10px] text-slate-400">Taxonomy & classification</div>
                    </div>
                  </Link>
                  <div className="my-1 border-t border-slate-100" />
                  <Link
                    to="/purchases"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="purchase-orders" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Purchase Orders</div>
                      <div className="text-[10px] text-slate-400">Supplier procurement orders</div>
                    </div>
                  </Link>
                  <Link
                    to="/suppliers"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="suppliers" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Suppliers</div>
                      <div className="text-[10px] text-slate-400">Vendor master directory</div>
                    </div>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* 3. Finance & Accounting */}
          <div className="relative">
            <button
              onClick={() => toggleDropdown('finance')}
              className={cn(
                'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md font-semibold transition-colors',
                isFinanceActive
                  ? 'bg-teal-50 text-teal-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              )}
            >
              <DollarSign className="w-3.5 h-3.5 text-teal-700" />
              <span>Accounting</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {activeDropdown === 'finance' && (
              <div className="absolute left-0 mt-1.5 w-60 bg-white border border-slate-200 rounded-xl shadow-xl py-2 z-50 animate-fade-in text-xs">
                <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100">
                  Financial Intelligence
                </div>
                <div className="py-1">
                  <Link
                    to="/dashboard"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="dashboard" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Executive Dashboard</div>
                      <div className="text-[10px] text-slate-400">KPIs, ledger charts & alerts</div>
                    </div>
                  </Link>
                  <Link
                    to="/invoices"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="invoices-billing" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Invoices & Receivables</div>
                      <div className="text-[10px] text-slate-400">Customer billing & tax records</div>
                    </div>
                  </Link>
                  <Link
                    to="/expenses"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="expenses" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Expenses</div>
                      <div className="text-[10px] text-slate-400">Operating vouchers & approvals</div>
                    </div>
                  </Link>
                  <Link
                    to="/payments"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="payments" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Payments</div>
                      <div className="text-[10px] text-slate-400">Bank settlements & receipts</div>
                    </div>
                  </Link>
                  <Link
                    to="/reports"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="financial-reports" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Financial Reports</div>
                      <div className="text-[10px] text-slate-400">P&L, balance sheets & audit</div>
                    </div>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* 4. AI & ML Forecasts */}
          <div className="relative">
            <button
              onClick={() => toggleDropdown('ml')}
              className={cn(
                'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md font-semibold transition-colors',
                isMlActive
                  ? 'bg-teal-50 text-teal-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              )}
            >
              <TrendingUp className="w-3.5 h-3.5 text-teal-700" />
              <span>Forecasts</span>
              <span className="hidden 2xl:inline-block px-1.5 py-0.2 text-[9px] font-bold rounded bg-purple-50 text-purple-700 border border-purple-200/60">
                ML
              </span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {activeDropdown === 'ml' && (
              <div className="absolute left-0 mt-1.5 w-68 bg-white border border-slate-200 rounded-xl shadow-xl py-2 z-50 animate-fade-in text-xs">
                <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 flex items-center justify-between">
                  <span>ML Prediction Engines</span>
                  <span className="text-[9px] text-purple-600 font-bold uppercase">Decision AI</span>
                </div>
                <div className="py-1">
                  <Link
                    to="/ml/revenue"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="revenue-forecast" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Revenue Forecast</div>
                      <div className="text-[10px] text-slate-400">XGBoost & SARIMA projections</div>
                    </div>
                  </Link>
                  <Link
                    to="/ml/sales"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="sales-demand" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Sales Demand Forecast</div>
                      <div className="text-[10px] text-slate-400">Product order volume prediction</div>
                    </div>
                  </Link>
                  <Link
                    to="/ml/inventory"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="inventory-reorder" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Inventory Reorder Intelligence</div>
                      <div className="text-[10px] text-slate-400">Replenishment recommendations</div>
                    </div>
                  </Link>
                  <Link
                    to="/ml/profit"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="profit-prediction" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Profit Margin Forecast</div>
                      <div className="text-[10px] text-slate-400">Gross & net margin trends</div>
                    </div>
                  </Link>
                  <Link
                    to="/ml/expense"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="expense-forecast" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Expense Forecast</div>
                      <div className="text-[10px] text-slate-400">Operating overhead prediction</div>
                    </div>
                  </Link>
                  <div className="my-1 border-t border-slate-100" />
                  <Link
                    to="/ml/business-health"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="business-health" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Business Health Score</div>
                      <div className="text-[10px] text-slate-400">Solvency & composite health metric</div>
                    </div>
                  </Link>
                  <Link
                    to="/ml/anomalies"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="anomaly-detection" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Transaction Anomalies</div>
                      <div className="text-[10px] text-slate-400">Outlier & fraud risk detection</div>
                    </div>
                  </Link>
                  <Link
                    to="/ml/chat"
                    className="flex items-center gap-2.5 px-3 py-2 text-teal-800 bg-teal-50/60 hover:bg-teal-50 transition-colors"
                  >
                    <ModuleIcon name="ai-copilot-voice" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-bold">AI Assistant Dedicated Page</div>
                      <div className="text-[10px] text-teal-700">Full-screen decision copilot</div>
                    </div>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* 5. Administration & Settings */}
          <div className="relative">
            <button
              onClick={() => toggleDropdown('admin')}
              className={cn(
                'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md font-semibold transition-colors',
                isAdminActive
                  ? 'bg-teal-50 text-teal-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              )}
            >
              <Settings className="w-3.5 h-3.5 text-slate-500" />
              <span>Admin</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {activeDropdown === 'admin' && (
              <div className="absolute left-0 mt-1.5 w-56 bg-white border border-slate-200 rounded-xl shadow-xl py-2 z-50 animate-fade-in text-xs">
                <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100">
                  Workspace Administration
                </div>
                <div className="py-1">
                  <Link
                    to="/companies"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="companies" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Companies</div>
                      <div className="text-[10px] text-slate-400">Entities & multi-tenancy</div>
                    </div>
                  </Link>
                  <Link
                    to="/branches"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="branches" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Branches</div>
                      <div className="text-[10px] text-slate-400">Branch offices & divisions</div>
                    </div>
                  </Link>
                  <Link
                    to="/users"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="users-roles" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Users & Roles</div>
                      <div className="text-[10px] text-slate-400">Permissions & user access</div>
                    </div>
                  </Link>
                  <Link
                    to="/notifications"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="notifications" size="sm" className="w-4 h-4 shrink-0" />
                    <div className="flex-1 flex items-center justify-between">
                      <div>
                        <div className="font-semibold">Notifications</div>
                        <div className="text-[10px] text-slate-400">Alerts & workflow triggers</div>
                      </div>
                      {typeof unreadCount === 'number' && unreadCount > 0 ? (
                        <span className="bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full ml-2">
                          {unreadCount}
                        </span>
                      ) : isUnreadCountError ? (
                        <span className="text-amber-500 text-[10px] font-bold ml-2" title="Notifications service temporarily unreachable">
                          •
                        </span>
                      ) : null}
                    </div>
                  </Link>
                  <Link
                    to="/settings"
                    className="flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-teal-800 transition-colors"
                  >
                    <ModuleIcon name="platform-settings" size="sm" className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Settings</div>
                      <div className="text-[10px] text-slate-400">Platform preferences</div>
                    </div>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Direct link to Import Center */}
          <Link
            to="/imports"
            className="hidden xl:flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-slate-700 hover:text-teal-800 hover:bg-slate-100 transition-colors font-semibold"
            title="Import CSV, Excel, or PDF Data"
          >
            <ModuleIcon name="data-import" size="xs" className="w-3.5 h-3.5 shrink-0" />
            <span>Import</span>
          </Link>

          {/* Direct link to AI Assistant Drawer */}
          <button
            onClick={onToggleAIAssistant}
            className="hidden xl:flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-teal-800 bg-teal-50/70 hover:bg-teal-100/80 transition-colors font-bold border border-teal-200/60"
            title="Open AI Decision Assistant Drawer"
          >
            <ModuleIcon name="ai-copilot-voice" size="xs" className="w-3.5 h-3.5 shrink-0" />
            <span>AI Copilot</span>
          </button>
        </nav>
      </div>

      {/* ── Right section: Global Search, Company Switcher, Notifications, Profile ── */}
      <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
        {/* Global Search Button (Ctrl+K) */}
        <button
          onClick={onOpenSearch}
          className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-xs text-slate-500 hover:border-slate-300 hover:bg-white hover:text-slate-700 transition-all shadow-2xs"
          title="Search commands, modules, records (Ctrl+K)"
        >
          <SearchIcon className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="hidden xl:inline">Search...</span>
          <kbd className="hidden sm:inline-block ml-0.5 px-1.5 py-0.5 text-[10px] font-mono rounded bg-slate-200 text-slate-600 border border-slate-300">
            ⌘K
          </kbd>
        </button>

        {/* Company / Workspace Switcher Dropdown */}
        <div className="relative hidden md:block" ref={companyRef}>
          <button
            onClick={() => setIsCompanyMenuOpen(!isCompanyMenuOpen)}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-800 transition-colors shadow-2xs"
            title="Current Organization Workspace"
          >
            <Building2 className="w-3.5 h-3.5 text-teal-700 shrink-0" />
            <span className="max-w-[85px] xl:max-w-[120px] truncate">
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

        {/* Branch / Outlet Switcher Dropdown */}
        <div className="relative hidden xl:block" ref={branchRef}>
          <button
            onClick={() => setIsBranchMenuOpen(!isBranchMenuOpen)}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-800 transition-colors shadow-2xs"
            title="Active Branch Outlet"
          >
            <GitBranch className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
            <span className="max-w-[85px] xl:max-w-[110px] truncate">
              {activeBranch?.name || 'All Outlets'}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {isBranchMenuOpen && (
            <div className="absolute right-0 mt-1.5 w-52 bg-white border border-slate-200 rounded-xl shadow-xl py-2 z-50 text-xs animate-fade-in">
              <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100">
                Select Branch Outlet
              </div>
              <div className="py-1 max-h-48 overflow-y-auto">
                <button
                  onClick={() => {
                    setActiveBranchId(null)
                    setIsBranchMenuOpen(false)
                  }}
                  className={cn(
                    'w-full text-left px-3 py-2 flex items-center justify-between transition-colors',
                    !activeBranchId
                      ? 'bg-teal-50 text-teal-800 font-semibold'
                      : 'text-slate-700 hover:bg-slate-50'
                  )}
                >
                  <span className="truncate">All Outlets (Consolidated)</span>
                  {!activeBranchId && <span className="w-1.5 h-1.5 rounded-full bg-teal-600" />}
                </button>
                {branches.map((b: any) => {
                  const isCurrent = activeBranchId === b.id
                  return (
                    <button
                      key={b.id}
                      onClick={() => {
                        setActiveBranchId(b.id)
                        setIsBranchMenuOpen(false)
                      }}
                      className={cn(
                        'w-full text-left px-3 py-2 flex items-center justify-between transition-colors',
                        isCurrent
                          ? 'bg-teal-50 text-teal-800 font-semibold'
                          : 'text-slate-700 hover:bg-slate-50'
                      )}
                    >
                      <span className="truncate">{b.name}</span>
                      {isCurrent && <span className="w-1.5 h-1.5 rounded-full bg-teal-600" />}
                    </button>
                  )
                })}
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
            <span className="absolute top-1 right-1 flex items-center justify-center min-w-4 h-4 px-1 rounded-full bg-teal-600 text-white text-[9px] font-bold animate-pulse">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Link>

        {/* User Profile Menu */}
        <div className="pl-1 border-l border-slate-200">
          <ProfileMenu />
        </div>
      </div>

      {/* ── Responsive Mobile Menu Overlay (Clean Top Modal, No Left Sidebar) ── */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 top-14 z-50 bg-slate-900/40 backdrop-blur-xs lg:hidden animate-fade-in flex flex-col justify-start">
          <div className="bg-white border-b border-slate-200 shadow-2xl max-h-[85vh] overflow-y-auto p-4 space-y-4">
            {/* Mobile Search input */}
            <div className="relative">
              <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search modules..."
                value={mobileSearch}
                onChange={(e) => setMobileSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
              />
            </div>

            {/* Quick App Launcher link */}
            <Link
              to="/apps"
              onClick={() => setIsMobileMenuOpen(false)}
              className="flex items-center gap-3 p-3 rounded-xl bg-teal-50 border border-teal-200/60 text-teal-900 font-bold text-xs"
            >
              <LayoutGrid className="w-5 h-5 text-teal-700" />
              <div>
                <div>Application Launcher</div>
                <div className="text-[10px] text-teal-700 font-normal">All ALLADIN modules & workflows</div>
              </div>
            </Link>

            {/* Grouped Links */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="space-y-1">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-1">
                  Sales & CRM
                </div>
                <Link
                  to="/sales"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="sales-orders" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Sales Orders</span>
                </Link>
                <Link
                  to="/invoices"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="invoices-billing" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Invoices</span>
                </Link>
                <Link
                  to="/customers"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="customers" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Customers</span>
                </Link>
                <Link
                  to="/payments"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="payments" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Payments</span>
                </Link>
              </div>

              <div className="space-y-1">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-1">
                  Inventory & Stock
                </div>
                <Link
                  to="/products"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="products-skus" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Products</span>
                </Link>
                <Link
                  to="/inventory"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="inventory" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Inventory</span>
                </Link>
                <Link
                  to="/purchases"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="purchase-orders" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Purchases</span>
                </Link>
                <Link
                  to="/warehouses"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="warehouses" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Warehouses</span>
                </Link>
              </div>

              <div className="space-y-1">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-1">
                  Finance & Reports
                </div>
                <Link
                  to="/dashboard"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="dashboard" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Dashboard</span>
                </Link>
                <Link
                  to="/expenses"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="expenses" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Expenses</span>
                </Link>
                <Link
                  to="/reports"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="financial-reports" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Reports</span>
                </Link>
              </div>

              <div className="space-y-1">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-1">
                  AI & Forecasts
                </div>
                <Link
                  to="/ml/revenue"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="revenue-forecast" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Revenue ML</span>
                </Link>
                <Link
                  to="/ml/chat"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-teal-800 font-semibold hover:bg-teal-50"
                >
                  <ModuleIcon name="ai-copilot-voice" size="sm" className="w-4 h-4 shrink-0" />
                  <span>AI Copilot</span>
                </Link>
                <Link
                  to="/ml/business-health"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-lg text-slate-700 hover:bg-slate-50"
                >
                  <ModuleIcon name="business-health" size="sm" className="w-4 h-4 shrink-0" />
                  <span>Health Score</span>
                </Link>
              </div>
            </div>

            {/* Close button */}
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <Link
                to="/help"
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-xs text-slate-500 hover:text-teal-700 flex items-center gap-1"
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Help & Documentation</span>
              </Link>
              <button
                onClick={() => setIsMobileMenuOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
