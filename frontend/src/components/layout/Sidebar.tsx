import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  ShoppingCart,
  Package,
  Receipt,
  Users,
  Building2,
  TrendingUp,
  BrainCircuit,
  AlertTriangle,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  PlusCircle,
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
  DollarSign,
  PieChart,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/hooks/useAuth'

export interface SidebarProps {
  isCollapsed: boolean
  onToggle: () => void
}

interface NavGroup {
  title: string
  items: {
    label: string
    href: string
    icon: React.ComponentType<{ className?: string }>
    badge?: string
  }[]
}

const navGroups: NavGroup[] = [
  {
    title: 'Core Platform',
    items: [
      { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { label: 'Companies', href: '/companies', icon: Building2 },
      { label: 'Branches', href: '/branches', icon: GitBranch },
      { label: 'Users & RBAC', href: '/users', icon: UserCheck },
      { label: 'Customers', href: '/customers', icon: Users },
      { label: 'Suppliers', href: '/suppliers', icon: Briefcase },
    ],
  },
  {
    title: 'Inventory & Products',
    items: [
      { label: 'Categories', href: '/categories', icon: Tag },
      { label: 'Products Catalog', href: '/products', icon: Package },
      { label: 'Warehouses', href: '/warehouses', icon: Warehouse },
      { label: 'Inventory Stock', href: '/inventory', icon: PackageCheck },
      { label: 'Stock Movements', href: '/stock-movements', icon: ArrowLeftRight },
    ],
  },
  {
    title: 'Commerce & Finance',
    items: [
      { label: 'Sales Orders', href: '/sales', icon: ShoppingCart },
      { label: 'Purchase Orders', href: '/purchases', icon: ShoppingBag },
      { label: 'Invoices & Billing', href: '/invoices', icon: Receipt },
      { label: 'Payments', href: '/payments', icon: CreditCard },
      { label: 'Expenses', href: '/expenses', icon: Layers },
      { label: 'Financial Reports', href: '/reports', icon: FileText },
    ],
  },
  {
    title: 'AI Intelligence Suite',
    items: [
      { label: 'Revenue Forecast', href: '/ml/revenue', icon: TrendingUp, badge: 'AI' },
      { label: 'Sales Forecast', href: '/ml/sales', icon: ShoppingCart, badge: 'AI' },
      { label: 'Inventory Demand', href: '/ml/inventory', icon: PackageCheck, badge: 'AI' },
      { label: 'Profit Prediction', href: '/ml/profit', icon: DollarSign, badge: 'AI' },
      { label: 'Expense Forecast', href: '/ml/expense', icon: PieChart, badge: 'AI' },
      { label: 'Business Health', href: '/ml/business-health', icon: BrainCircuit, badge: 'AI' },
      { label: 'Anomaly Detection', href: '/ml/anomalies', icon: AlertTriangle, badge: 'AI' },
      { label: 'AI Assistant Chat', href: '/ml/chat', icon: FileText, badge: 'AI' },
    ],
  },
  {
    title: 'System & Admin',
    items: [
      { label: 'Notifications', href: '/notifications', icon: Bell },
      { label: 'System Settings', href: '/settings', icon: Settings },
    ],
  },
]

export const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggle }) => {
  const { activeCompany, companies, setActiveCompanyId } = useAuth()

  return (
    <aside
      className={cn(
        'fixed top-0 left-0 z-30 h-screen bg-white dark:bg-surface-900 border-r border-surface-200 dark:border-surface-800 transition-all duration-300 flex flex-col',
        isCollapsed ? 'w-[68px]' : 'w-[260px]'
      )}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-[60px] px-4 border-b border-surface-200 dark:border-surface-800">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-primary-600 to-indigo-500 text-white font-bold text-lg shadow-md shrink-0">
            F
          </div>
          {!isCollapsed && (
            <div className="flex flex-col truncate">
              <span className="font-bold text-sm tracking-tight text-surface-900 dark:text-surface-100 truncate">
                FinIntel AI
              </span>
              <span className="text-[10px] text-surface-400 font-medium tracking-wider uppercase">
                Enterprise ERP
              </span>
            </div>
          )}
        </div>
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-surface-200 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Multi-Tenant Company Selector */}
      <div className="p-3 border-b border-surface-200 dark:border-surface-800">
        {!isCollapsed ? (
          <div className="relative">
            <select
              value={activeCompany?.company_id || ''}
              onChange={(e) => setActiveCompanyId(e.target.value)}
              className="w-full pl-8 pr-3 py-2 text-xs font-semibold rounded-lg border border-surface-200 dark:border-surface-700 bg-surface-50 dark:bg-surface-800 text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none cursor-pointer truncate"
            >
              {companies.map((c) => (
                <option key={c.company_id} value={c.company_id}>
                  {c.company_name}
                </option>
              ))}
            </select>
            <Briefcase className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-surface-400 pointer-events-none" />
          </div>
        ) : (
          <div
            className="flex items-center justify-center w-10 h-10 mx-auto rounded-lg bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 font-bold text-xs"
            title={activeCompany?.company_name || 'Company'}
          >
            {activeCompany?.company_name?.charAt(0).toUpperCase() || 'C'}
          </div>
        )}
      </div>

      {/* Nav Groups */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navGroups.map((group) => (
          <div key={group.title} className="space-y-1">
            {!isCollapsed && (
              <h4 className="px-3 text-[10px] font-bold text-surface-400 dark:text-surface-500 uppercase tracking-wider mb-2">
                {group.title}
              </h4>
            )}
            {group.items.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 px-3 py-2 text-xs font-medium transition-colors group relative rounded-lg',
                      isActive
                        ? 'bg-primary-50 dark:bg-primary-950/50 text-primary-600 dark:text-primary-400 font-semibold'
                        : 'text-surface-600 dark:text-surface-400 hover:text-surface-900 dark:hover:text-surface-100 hover:bg-surface-100 dark:hover:bg-surface-800'
                    )
                  }
                  title={isCollapsed ? item.label : undefined}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {!isCollapsed && <span className="truncate">{item.label}</span>}
                  {!isCollapsed && item.badge && (
                    <span className="ml-auto px-1.5 py-0.5 text-[9px] font-bold rounded-md bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              )
            })}
          </div>
        ))}
      </div>

      {/* Footer item */}
      {!isCollapsed && (
        <div className="p-3 border-t border-surface-200 dark:border-surface-800">
          <NavLink
            to="/onboard"
            className="flex items-center justify-center gap-2 w-full py-2 text-xs font-medium rounded-lg border border-dashed border-surface-300 dark:border-surface-700 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors"
          >
            <PlusCircle className="w-4 h-4 text-primary-600" />
            <span>Add New Company</span>
          </NavLink>
        </div>
      )}
    </aside>
  )
}
