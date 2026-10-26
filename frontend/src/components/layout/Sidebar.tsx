import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  ChevronLeft,
  ChevronRight,
  PlusCircle,
} from 'lucide-react'
import { ModuleIcon, ModuleIconName } from '@/components/ui/ModuleIcon'
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
    moduleIcon: ModuleIconName
    badge?: string
  }[]
}

const navGroups: NavGroup[] = [
  {
    title: 'Operations & Commercial',
    items: [
      { label: 'Overview', href: '/dashboard', moduleIcon: 'dashboard' },
      { label: 'Data Import Center', href: '/imports', moduleIcon: 'data-import', badge: 'New' },
      { label: 'Sales Orders', href: '/sales', moduleIcon: 'sales-orders' },
      { label: 'Invoices & Billing', href: '/invoices', moduleIcon: 'invoices-billing' },
      { label: 'Customer Directory', href: '/customers', moduleIcon: 'customers' },
      { label: 'Payments', href: '/payments', moduleIcon: 'payments' },
      { label: 'Operating Expenses', href: '/expenses', moduleIcon: 'expenses' },
    ],
  },
  {
    title: 'Procurement & Inventory',
    items: [
      { label: 'Products & SKUs', href: '/products', moduleIcon: 'products-skus' },
      { label: 'Inventory Balances', href: '/inventory', moduleIcon: 'inventory' },
      { label: 'Stock Movements', href: '/stock-movements', moduleIcon: 'stock-movements' },
      { label: 'Warehouses', href: '/warehouses', moduleIcon: 'warehouses' },
      { label: 'Categories', href: '/categories', moduleIcon: 'categories' },
      { label: 'Purchase Orders', href: '/purchases', moduleIcon: 'purchase-orders' },
      { label: 'Suppliers Directory', href: '/suppliers', moduleIcon: 'suppliers' },
    ],
  },
  {
    title: 'Forecasting & ML Suite',
    items: [
      { label: 'Revenue Forecast', href: '/ml/revenue', moduleIcon: 'revenue-forecast', badge: 'ML' },
      { label: 'Sales Demand', href: '/ml/sales', moduleIcon: 'sales-demand', badge: 'ML' },
      { label: 'Inventory Reorder', href: '/ml/inventory', moduleIcon: 'inventory-reorder', badge: 'ML' },
      { label: 'Profit Prediction', href: '/ml/profit', moduleIcon: 'profit-prediction', badge: 'ML' },
      { label: 'Expense Forecast', href: '/ml/expense', moduleIcon: 'expense-forecast', badge: 'ML' },
      { label: 'Business Health', href: '/ml/business-health', moduleIcon: 'business-health', badge: 'ML' },
      { label: 'Anomaly Detection', href: '/ml/anomalies', moduleIcon: 'anomaly-detection', badge: 'ML' },
      { label: 'Conversational Copilot', href: '/ml/chat', moduleIcon: 'ai-copilot-voice', badge: 'AI' },
    ],
  },
  {
    title: 'Organization & Admin',
    items: [
      { label: 'Companies', href: '/companies', moduleIcon: 'companies' },
      { label: 'Branches', href: '/branches', moduleIcon: 'branches' },
      { label: 'Users & Permissions', href: '/users', moduleIcon: 'users-roles' },
      { label: 'Financial Reports', href: '/reports', moduleIcon: 'financial-reports' },
      { label: 'Notifications', href: '/notifications', moduleIcon: 'notifications' },
      { label: 'Company Settings', href: '/settings', moduleIcon: 'platform-settings' },
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
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-2.5 px-2.5 py-1.5 text-xs font-medium rounded-lg transition-all relative group',
                      isActive
                        ? 'bg-teal-50 text-teal-900 font-semibold border-l-2 border-teal-700 pl-2 shadow-2xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50/80'
                    )
                  }
                  title={isCollapsed ? item.label : undefined}
                >
                  <ModuleIcon
                    name={item.moduleIcon}
                    size="xs"
                    alt={item.label}
                    className="w-4 h-4 shrink-0 transition-transform group-hover:scale-110"
                  />
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
            className="flex items-center justify-center gap-1.5 w-full py-1.5 text-xs font-medium rounded-lg border border-dashed border-slate-300 text-slate-600 hover:border-teal-400 hover:text-teal-800 hover:bg-white transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5 text-teal-700" />
            <span>Add Organization</span>
          </NavLink>
        </div>
      )}
    </aside>
  )
}
