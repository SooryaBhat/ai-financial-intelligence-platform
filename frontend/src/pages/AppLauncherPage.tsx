import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ShoppingCart,
  Package,
  Receipt,
  Users,
  Building2,
  TrendingUp,
  AlertTriangle,
  FileText,
  Settings,
  Briefcase,
  Layers,
  GitBranch,
  UserCheck,
  Tag,
  Warehouse,
  PackageCheck,
  ArrowLeftRight,
  ShoppingBag,
  CreditCard,
  Bell,
  PieChart,
  Bot,
  Search,
  DollarSign,
  HeartPulse,
  LayoutDashboard,
  Sparkles,
  UploadCloud,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { reportService } from '@/services/erp.service'
import { formatCurrency } from '@/lib/utils'
import { Skeleton } from '@/components/ui/Skeleton'
import { cn } from '@/lib/utils'

interface AppModule {
  id: string
  label: string
  description: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  bg: string
  border: string
  badge?: string
  group: string
}

const appModules: AppModule[] = [
  // Operations & Commercial
  {
    id: 'dashboard',
    label: 'Dashboard',
    description: 'KPIs, charts & operational intelligence',
    href: '/dashboard',
    icon: LayoutDashboard,
    color: 'text-teal-700',
    bg: 'bg-teal-50',
    border: 'border-teal-200',
    group: 'Operations',
  },
  {
    id: 'imports',
    label: 'Data Import Center',
    description: 'Bulk CSV, Excel & PDF extraction with validation',
    href: '/imports',
    icon: UploadCloud,
    color: 'text-indigo-700',
    bg: 'bg-indigo-50',
    border: 'border-indigo-200',
    badge: 'Step 7',
    group: 'Operations',
  },
  {
    id: 'sales',
    label: 'Sales Orders',
    description: 'Customer orders & commercial pipeline',
    href: '/sales',
    icon: ShoppingCart,
    color: 'text-emerald-700',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    group: 'Operations',
  },
  {
    id: 'invoices',
    label: 'Invoices & Billing',
    description: 'Customer invoices & receivables ledger',
    href: '/invoices',
    icon: Receipt,
    color: 'text-blue-700',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    group: 'Operations',
  },
  {
    id: 'customers',
    label: 'Customers',
    description: 'Customer accounts & CRM directory',
    href: '/customers',
    icon: Users,
    color: 'text-violet-700',
    bg: 'bg-violet-50',
    border: 'border-violet-200',
    group: 'Operations',
  },
  {
    id: 'payments',
    label: 'Payments',
    description: 'Payment records & settlement tracker',
    href: '/payments',
    icon: CreditCard,
    color: 'text-sky-700',
    bg: 'bg-sky-50',
    border: 'border-sky-200',
    group: 'Operations',
  },
  {
    id: 'expenses',
    label: 'Expenses',
    description: 'Operating expense vouchers & approvals',
    href: '/expenses',
    icon: Layers,
    color: 'text-orange-700',
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    group: 'Operations',
  },

  // Procurement & Inventory
  {
    id: 'products',
    label: 'Products & SKUs',
    description: 'Product master catalog & price lists',
    href: '/products',
    icon: Package,
    color: 'text-indigo-700',
    bg: 'bg-indigo-50',
    border: 'border-indigo-200',
    group: 'Inventory',
  },
  {
    id: 'inventory',
    label: 'Inventory',
    description: 'Real-time stock balances & locations',
    href: '/inventory',
    icon: PackageCheck,
    color: 'text-teal-700',
    bg: 'bg-teal-50',
    border: 'border-teal-200',
    group: 'Inventory',
  },
  {
    id: 'stock-movements',
    label: 'Stock Movements',
    description: 'In/out movements, transfers & logs',
    href: '/stock-movements',
    icon: ArrowLeftRight,
    color: 'text-slate-700',
    bg: 'bg-slate-100',
    border: 'border-slate-200',
    group: 'Inventory',
  },
  {
    id: 'warehouses',
    label: 'Warehouses',
    description: 'Storage facility & zone management',
    href: '/warehouses',
    icon: Warehouse,
    color: 'text-amber-700',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    group: 'Inventory',
  },
  {
    id: 'categories',
    label: 'Categories',
    description: 'Product classification & taxonomy',
    href: '/categories',
    icon: Tag,
    color: 'text-rose-700',
    bg: 'bg-rose-50',
    border: 'border-rose-200',
    group: 'Inventory',
  },
  {
    id: 'purchases',
    label: 'Purchase Orders',
    description: 'Vendor orders & procurement workflow',
    href: '/purchases',
    icon: ShoppingBag,
    color: 'text-cyan-700',
    bg: 'bg-cyan-50',
    border: 'border-cyan-200',
    group: 'Inventory',
  },
  {
    id: 'suppliers',
    label: 'Suppliers',
    description: 'Approved vendor master directory',
    href: '/suppliers',
    icon: Briefcase,
    color: 'text-stone-700',
    bg: 'bg-stone-100',
    border: 'border-stone-200',
    group: 'Inventory',
  },

  // AI & ML Intelligence
  {
    id: 'ml-revenue',
    label: 'Revenue Forecast',
    description: 'XGBoost & SARIMA revenue projections',
    href: '/ml/revenue',
    icon: TrendingUp,
    color: 'text-purple-700',
    bg: 'bg-purple-50',
    border: 'border-purple-200',
    badge: 'ML',
    group: 'Intelligence',
  },
  {
    id: 'ml-sales',
    label: 'Sales Demand',
    description: 'Demand forecasting & pipeline prediction',
    href: '/ml/sales',
    icon: ShoppingCart,
    color: 'text-emerald-700',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    badge: 'ML',
    group: 'Intelligence',
  },
  {
    id: 'ml-inventory',
    label: 'Inventory Reorder',
    description: 'AI replenishment recommendations',
    href: '/ml/inventory',
    icon: PackageCheck,
    color: 'text-blue-700',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    badge: 'ML',
    group: 'Intelligence',
  },
  {
    id: 'ml-profit',
    label: 'Profit Prediction',
    description: 'Margin trajectory & profitability models',
    href: '/ml/profit',
    icon: DollarSign,
    color: 'text-teal-700',
    bg: 'bg-teal-50',
    border: 'border-teal-200',
    badge: 'ML',
    group: 'Intelligence',
  },
  {
    id: 'ml-expense',
    label: 'Expense Forecast',
    description: 'Operating cost forecast & trend model',
    href: '/ml/expense',
    icon: PieChart,
    color: 'text-orange-700',
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    badge: 'ML',
    group: 'Intelligence',
  },
  {
    id: 'ml-health',
    label: 'Business Health',
    description: 'Composite health score & risk rating',
    href: '/ml/business-health',
    icon: HeartPulse,
    color: 'text-rose-700',
    bg: 'bg-rose-50',
    border: 'border-rose-200',
    badge: 'ML',
    group: 'Intelligence',
  },
  {
    id: 'ml-anomalies',
    label: 'Anomaly Detection',
    description: 'Transaction outlier & fraud alerts',
    href: '/ml/anomalies',
    icon: AlertTriangle,
    color: 'text-amber-700',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    badge: 'ML',
    group: 'Intelligence',
  },
  {
    id: 'ml-chat',
    label: 'AI Copilot & Voice',
    description: 'Conversational voice & text ERP intelligence assistant',
    href: '/ml/chat',
    icon: Bot,
    color: 'text-teal-700',
    bg: 'bg-teal-50',
    border: 'border-teal-300',
    badge: 'Voice & AI',
    group: 'Intelligence',
  },

  // Organization & Admin
  {
    id: 'companies',
    label: 'Companies',
    description: 'Multi-entity enterprise workspaces',
    href: '/companies',
    icon: Building2,
    color: 'text-slate-700',
    bg: 'bg-slate-100',
    border: 'border-slate-200',
    group: 'Admin',
  },
  {
    id: 'branches',
    label: 'Branches',
    description: 'Branch offices & regional divisions',
    href: '/branches',
    icon: GitBranch,
    color: 'text-indigo-700',
    bg: 'bg-indigo-50',
    border: 'border-indigo-200',
    group: 'Admin',
  },
  {
    id: 'users',
    label: 'Users & Roles',
    description: 'User access control & permissions',
    href: '/users',
    icon: UserCheck,
    color: 'text-violet-700',
    bg: 'bg-violet-50',
    border: 'border-violet-200',
    group: 'Admin',
  },
  {
    id: 'reports',
    label: 'Financial Reports',
    description: 'P&L, balance sheets & audit trails',
    href: '/reports',
    icon: FileText,
    color: 'text-blue-700',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    group: 'Admin',
  },
  {
    id: 'notifications',
    label: 'Notifications',
    description: 'System alerts & workflow updates',
    href: '/notifications',
    icon: Bell,
    color: 'text-amber-700',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    group: 'Admin',
  },
  {
    id: 'settings',
    label: 'Platform Settings',
    description: 'Company parameters & configuration',
    href: '/settings',
    icon: Settings,
    color: 'text-slate-700',
    bg: 'bg-slate-100',
    border: 'border-slate-200',
    group: 'Admin',
  },
]

const groupOrder = ['Operations', 'Inventory', 'Intelligence', 'Admin']
const groupLabels: Record<string, string> = {
  Operations: 'Operations & Commercial',
  Inventory: 'Procurement & Inventory',
  Intelligence: 'AI & ML Intelligence Suite',
  Admin: 'Organisation & Administration',
}
const groupDescriptions: Record<string, string> = {
  Operations: 'Sales orders, invoices, customer directories, payments and expenses',
  Inventory: 'Products, stock levels, warehouses, purchases and suppliers',
  Intelligence: 'Machine-learning forecasts and AI-powered decision models',
  Admin: 'Company entities, branches, user roles, reports and settings',
}

export const AppLauncherPage: React.FC = () => {
  const navigate = useNavigate()
  const { user, activeCompany } = useAuth()
  const [search, setSearch] = useState('')

  const { data: summary, isLoading } = useQuery({
    queryKey: ['dashboard-summary', activeCompany?.id || activeCompany?.company_id],
    queryFn: () => reportService.getSummary(),
    staleTime: 5 * 60 * 1000,
  })

  const filteredModules = appModules.filter(
    (m) =>
      !search ||
      m.label.toLowerCase().includes(search.toLowerCase()) ||
      m.description.toLowerCase().includes(search.toLowerCase())
  )

  const grouped = groupOrder
    .map((g) => ({
      key: g,
      label: groupLabels[g],
      description: groupDescriptions[g],
      modules: filteredModules.filter((m) => m.group === g),
    }))
    .filter((g) => g.modules.length > 0)

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ── Welcome / Hero Header (Crisp White/Light Enterprise Theme) ── */}
      <div className="relative overflow-hidden rounded-2xl bg-white border border-slate-200 p-6 sm:p-8 shadow-sm">
        {/* Subtle decorative background accents in teal / slate */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-teal-50/60 via-slate-50/30 to-transparent rounded-full -mr-20 -mt-20 pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider rounded-full bg-teal-50 text-teal-800 border border-teal-200/80">
                <Sparkles className="w-3 h-3 text-teal-600" />
                {activeCompany?.company_name || 'Enterprise Workspace'}
              </span>
              <span className="text-xs text-slate-400 font-medium">&bull; FY 2026</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Good {getTimeGreeting()},{' '}
              <span className="text-teal-700">{user?.full_name?.split(' ')[0] || 'Administrator'}</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 leading-relaxed">
              Welcome to the ALLADIN ERP application launcher. Launch commercial operations, track warehouse inventory, and consult ML intelligence models.
            </p>
          </div>

          {/* Quick Metrics Ribbon (White & Light Theme) */}
          <div className="flex items-center gap-3 shrink-0 flex-wrap sm:flex-nowrap">
            <div
              onClick={() => navigate('/invoices')}
              className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-white hover:border-teal-300 transition-all cursor-pointer min-w-[130px]"
            >
              <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Total Revenue</div>
              {isLoading ? (
                <Skeleton className="h-6 w-24 mt-1" />
              ) : (
                <div className="text-base font-extrabold text-slate-900 mt-0.5">
                  {formatCurrency(summary?.total_revenue ?? 129091501.22)}
                </div>
              )}
            </div>

            <div
              onClick={() => navigate('/ml/profit')}
              className="p-3.5 rounded-xl border border-teal-100 bg-teal-50/50 hover:bg-teal-50 hover:border-teal-300 transition-all cursor-pointer min-w-[130px]"
            >
              <div className="text-[10px] text-teal-700 font-bold uppercase tracking-wider">Net Profit</div>
              {isLoading ? (
                <Skeleton className="h-6 w-24 mt-1" />
              ) : (
                <div className="text-base font-extrabold text-teal-800 mt-0.5">
                  {formatCurrency(summary?.net_profit ?? 46272220.09)}
                </div>
              )}
            </div>

            <div
              onClick={() => navigate('/dashboard')}
              className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-white hover:border-teal-300 transition-all cursor-pointer min-w-[110px]"
            >
              <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Executive View</div>
              <div className="text-xs font-bold text-teal-700 mt-1 flex items-center gap-1">
                <span>Dashboard</span>
                <span>&rarr;</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Search filter & Quick Bar ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="relative max-w-sm w-full">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search modules (e.g. Sales, Inventory, ML)..."
            className="w-full pl-10 pr-4 py-2 text-xs sm:text-sm border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-shadow placeholder:text-slate-400 shadow-2xs"
          />
        </div>
        <div className="text-xs text-slate-400 font-medium">
          Showing {filteredModules.length} operational modules
        </div>
      </div>

      {/* ── Module Groups Grid ── */}
      {grouped.map((group) => (
        <section key={group.key} className="space-y-3.5">
          <div className="flex items-baseline gap-2.5 pb-1 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900 tracking-tight">{group.label}</h2>
            <span className="text-xs text-slate-400 font-normal hidden sm:inline">&bull; {group.description}</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
            {group.modules.map((mod) => {
              const Icon = mod.icon
              return (
                <Link
                  key={mod.id}
                  to={mod.href}
                  className={cn(
                    'group flex items-start gap-3.5 p-4 rounded-xl border border-slate-200 bg-white shadow-2xs',
                    'hover:shadow-md hover:border-teal-300 hover:-translate-y-0.5 transition-all duration-150',
                    'focus:outline-none focus:ring-2 focus:ring-teal-500 select-none'
                  )}
                >
                  {/* Module icon container */}
                  <div
                    className={cn(
                      'w-11 h-11 rounded-xl flex items-center justify-center border shrink-0 transition-transform group-hover:scale-105',
                      mod.bg,
                      mod.border
                    )}
                  >
                    <Icon className={cn('w-5 h-5', mod.color)} />
                  </div>

                  {/* Module info */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-xs sm:text-sm font-bold text-slate-900 group-hover:text-teal-800 transition-colors">
                        {mod.label}
                      </span>
                      {mod.badge && (
                        <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded bg-teal-50 text-teal-800 border border-teal-200/80 leading-none">
                          {mod.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1 leading-snug line-clamp-2">
                      {mod.description}
                    </p>
                  </div>

                  {/* Subtle hover chevron */}
                  <div className="text-slate-300 group-hover:text-teal-600 transition-colors shrink-0 mt-1">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </Link>
              )
            })}
          </div>
        </section>
      ))}

      {/* Empty search state */}
      {grouped.length === 0 && (
        <div className="text-center py-16 bg-white border border-slate-200 rounded-2xl p-8">
          <Search className="w-10 h-10 mx-auto mb-3 text-slate-300" />
          <h3 className="text-sm font-bold text-slate-700">No modules found</h3>
          <p className="text-xs text-slate-400 mt-1">
            No application modules match &ldquo;{search}&rdquo;
          </p>
          <button
            onClick={() => setSearch('')}
            className="mt-3 px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-lg transition-colors"
          >
            Clear search filter
          </button>
        </div>
      )}
    </div>
  )
}

function getTimeGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'morning'
  if (h < 17) return 'afternoon'
  return 'evening'
}
