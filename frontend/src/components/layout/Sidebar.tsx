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
  PieChart,
  Bot,
} from 'lucide-react'
import { cn } from '@/lib/utils'

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
    title: 'Operations & Commercial',
    items: [
      { label: 'Overview', href: '/dashboard', icon: LayoutDashboard },
      { label: 'Sales Orders', href: '/sales', icon: ShoppingCart },
      { label: 'Invoices & Billing', href: '/invoices', icon: Receipt },
      { label: 'Customer Directory', href: '/customers', icon: Users },
      { label: 'Payments', href: '/payments', icon: CreditCard },
      { label: 'Operating Expenses', href: '/expenses', icon: Layers },
    ],
  },
  {
    title: 'Procurement & Inventory',
    items: [
      { label: 'Products & SKUs', href: '/products', icon: Package },
      { label: 'Inventory Balances', href: '/inventory', icon: PackageCheck },
      { label: 'Stock Movements', href: '/stock-movements', icon: ArrowLeftRight },
      { label: 'Warehouses', href: '/warehouses', icon: Warehouse },
      { label: 'Categories', href: '/categories', icon: Tag },
      { label: 'Purchase Orders', href: '/purchases', icon: ShoppingBag },
      { label: 'Suppliers Directory', href: '/suppliers', icon: Briefcase },
    ],
  },
  {
    title: 'Forecasting & ML Suite',
    items: [
      { label: 'Revenue Forecast', href: '/ml/revenue', icon: TrendingUp, badge: 'ML' },
      { label: 'Sales Demand', href: '/ml/sales', icon: ShoppingCart, badge: 'ML' },
      { label: 'Inventory Reorder', href: '/ml/inventory', icon: PackageCheck, badge: 'ML' },
      { label: 'Profit Prediction', href: '/ml/profit', icon: TrendingUp, badge: 'ML' },
      { label: 'Expense Forecast', href: '/ml/expense', icon: PieChart, badge: 'ML' },
      { label: 'Business Health', href: '/ml/business-health', icon: BrainCircuit, badge: 'ML' },
      { label: 'Anomaly Detection', href: '/ml/anomalies', icon: AlertTriangle, badge: 'ML' },
      { label: 'Conversational Copilot', href: '/ml/chat', icon: Bot, badge: 'AI' },
    ],
  },
  {
    title: 'Organization & Admin',
    items: [
      { label: 'Companies', href: '/companies', icon: Building2 },
      { label: 'Branches', href: '/branches', icon: GitBranch },
      { label: 'Users & Permissions', href: '/users', icon: UserCheck },
      { label: 'Financial Reports', href: '/reports', icon: FileText },
      { label: 'Notifications', href: '/notifications', icon: Bell },
      { label: 'Company Settings', href: '/settings', icon: Settings },
    ],
  },
]

export const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggle }) => {
  return (
    <aside
      className={cn(
        'fixed top-14 left-0 z-20 h-[calc(100vh-3.5rem)] bg-white border-r border-slate-200 transition-all duration-200 flex flex-col',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Sidebar Header / Section indicator */}
      <div className="flex items-center justify-between h-10 px-3 border-b border-slate-100 bg-slate-50/60">
        {!isCollapsed && (
          <span className="text-[10px] font-bold tracking-wider uppercase text-slate-500">
            Workspaces & Modules
          </span>
        )}
        <button
          onClick={onToggle}
          className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors ml-auto"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Nav Groups Navigation List */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        {navGroups.map((group) => (
          <div key={group.title} className="space-y-0.5">
            {!isCollapsed && (
              <h4 className="px-2.5 pt-1 pb-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
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
                      'flex items-center gap-2.5 px-2.5 py-1.5 text-xs font-medium rounded-md transition-colors relative group',
                      isActive
                        ? 'bg-teal-50 text-teal-900 font-semibold border-l-2 border-teal-700 pl-2'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                    )
                  }
                  title={isCollapsed ? item.label : undefined}
                >
                  <Icon className="w-4 h-4 shrink-0 text-slate-500 group-hover:text-teal-700" />
                  {!isCollapsed && <span className="truncate">{item.label}</span>}
                  {!isCollapsed && item.badge && (
                    <span className="ml-auto px-1.5 py-0.2 text-[9px] font-semibold rounded bg-teal-50 text-teal-700 border border-teal-200/60">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              )
            })}
          </div>
        ))}
      </div>

      {/* Footer link for Quick Company Setup */}
      {!isCollapsed && (
        <div className="p-2 border-t border-slate-100 bg-slate-50/50">
          <NavLink
            to="/onboard"
            className="flex items-center justify-center gap-1.5 w-full py-1.5 text-xs font-medium rounded border border-dashed border-slate-300 text-slate-600 hover:border-teal-400 hover:text-teal-800 hover:bg-white transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5 text-teal-700" />
            <span>Add Organization</span>
          </NavLink>
        </div>
      )}
    </aside>
  )
}
