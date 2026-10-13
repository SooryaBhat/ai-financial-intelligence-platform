import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search,
  LayoutDashboard,
  ShoppingCart,
  Package,
  Receipt,
  Users,
  Building2,
  TrendingUp,
  BrainCircuit,
  Bot,
  FileText,
  Settings,
  HelpCircle,
  PlusCircle,
  CreditCard,
  Warehouse,
  ArrowRight,
  X,
} from 'lucide-react'

interface CommandItem {
  id: string
  title: string
  category: 'ERP Modules' | 'Forecasting & ML' | 'Quick Actions' | 'Help & Documentation'
  description?: string
  href?: string
  action?: () => void
  icon: React.ComponentType<{ className?: string }>
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  onOpenAIAssistant?: () => void
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onOpenAIAssistant,
}) => {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const commandItems: CommandItem[] = [
    // ERP Modules
    { id: 'dashboard', title: 'Dashboard & Overview', category: 'ERP Modules', description: 'Real-time telemetry and KPI overview', href: '/dashboard', icon: LayoutDashboard },
    { id: 'sales', title: 'Sales Orders', category: 'ERP Modules', description: 'Customer sales orders and commercial transactions', href: '/sales', icon: ShoppingCart },
    { id: 'invoices', title: 'Invoices & Billing', category: 'ERP Modules', description: 'Accounts receivable, tax invoices, and credit notes', href: '/invoices', icon: Receipt },
    { id: 'products', title: 'Product Catalog & SKUs', category: 'ERP Modules', description: 'Price lists, cost prices, and SKU definitions', href: '/products', icon: Package },
    { id: 'inventory', title: 'Inventory Stock Levels', category: 'ERP Modules', description: 'On-hand quantities across all warehouses', href: '/inventory', icon: Warehouse },
    { id: 'purchases', title: 'Purchase Orders', category: 'ERP Modules', description: 'Procurement orders and vendor deliveries', href: '/purchases', icon: ShoppingCart },
    { id: 'customers', title: 'Customer Directory', category: 'ERP Modules', description: 'Customer accounts, contacts, and balances', href: '/customers', icon: Users },
    { id: 'suppliers', title: 'Supplier Directory', category: 'ERP Modules', description: 'Approved vendor lists and procurement contacts', href: '/suppliers', icon: Users },
    { id: 'expenses', title: 'Operational Expenses', category: 'ERP Modules', description: 'Expense tracking and ledger categorization', href: '/expenses', icon: Receipt },
    { id: 'payments', title: 'Payments & Collections', category: 'ERP Modules', description: 'Bank settlements and payment vouchers', href: '/payments', icon: CreditCard },
    { id: 'companies', title: 'Company Profiles', category: 'ERP Modules', description: 'Multi-tenant organization structures', href: '/companies', icon: Building2 },
    { id: 'reports', title: 'Financial Reports', category: 'ERP Modules', description: 'Profit & Loss, balance sheets, and audit trails', href: '/reports', icon: FileText },
    { id: 'settings', title: 'Platform Settings', category: 'ERP Modules', description: 'Company preferences, tax rules, and currency', href: '/settings', icon: Settings },

    // Forecasting & ML
    { id: 'ml-revenue', title: 'Revenue Forecast', category: 'Forecasting & ML', description: 'XGBoost & SARIMA monthly revenue predictions', href: '/ml/revenue', icon: TrendingUp },
    { id: 'ml-sales', title: 'Sales Demand Forecast', category: 'Forecasting & ML', description: 'Predict product demand and seasonal surges', href: '/ml/sales', icon: ShoppingCart },
    { id: 'ml-inventory', title: 'Inventory Reorder Intelligence', category: 'Forecasting & ML', description: 'Stockout risk evaluation and safety thresholds', href: '/ml/inventory', icon: Package },
    { id: 'ml-profit', title: 'Profit Margin Prediction', category: 'Forecasting & ML', description: 'Net and gross margin projection models', href: '/ml/profit', icon: TrendingUp },
    { id: 'ml-expense', title: 'Expense Prediction', category: 'Forecasting & ML', description: 'Operating expense forecast per department', href: '/ml/expense', icon: Receipt },
    { id: 'ml-health', title: 'Business Health Score', category: 'Forecasting & ML', description: 'Composite financial health evaluation (0-100)', href: '/ml/business-health', icon: BrainCircuit },
    { id: 'ml-anomalies', title: 'Anomaly Detection', category: 'Forecasting & ML', description: 'Isolation Forest transaction anomaly scans', href: '/ml/anomalies', icon: BrainCircuit },

    // Quick Actions
    {
      id: 'ask-ai',
      title: 'Ask ALLADIN AI Copilot',
      category: 'Quick Actions',
      description: 'Open persistent conversational AI assistant',
      action: () => {
        onClose()
        if (onOpenAIAssistant) onOpenAIAssistant()
      },
      icon: Bot,
    },
    {
      id: 'create-invoice',
      title: 'Create New Invoice',
      category: 'Quick Actions',
      description: 'Issue sales invoice for customer order',
      href: '/invoices',
      icon: PlusCircle,
    },
    {
      id: 'add-product',
      title: 'Add New Product SKU',
      category: 'Quick Actions',
      description: 'Catalog entry with selling & cost prices',
      href: '/products',
      icon: PlusCircle,
    },

    // Help & Docs
    { id: 'help-docs', title: 'ALLADIN Documentation & User Guide', category: 'Help & Documentation', description: 'ERP workflows, ML model details, and FAQs', href: '/help', icon: HelpCircle },
  ]

  const filtered = commandItems.filter((item) => {
    const text = `${item.title} ${item.description || ''} ${item.category}`.toLowerCase()
    return text.includes(query.toLowerCase())
  })

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        inputRef.current?.focus()
      }, 50)
    } else {
      setQuery('')
    }
  }, [isOpen])

  const executeCommand = React.useCallback(
    (item: CommandItem) => {
      onClose()
      if (item.action) {
        item.action()
      } else if (item.href) {
        navigate(item.href)
      }
    },
    [onClose, navigate]
  )

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        if (isOpen) onClose()
        else {
          // Open triggered by parent if wired
        }
      }
      if (!isOpen) return

      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev < filtered.length - 1 ? prev + 1 : 0))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : filtered.length - 1))
      } else if (e.key === 'Enter') {
        e.preventDefault()
        const selected = filtered[selectedIndex]
        if (selected) {
          executeCommand(selected)
        }
      } else if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, filtered, selectedIndex, onClose, executeCommand])

  if (!isOpen) return null

  // Group filtered results
  const grouped = filtered.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = []
    acc[item.category].push(item)
    return acc
  }, {} as Record<string, CommandItem[]>)

  let globalCounter = 0

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto p-4 sm:p-6 md:p-20 flex items-start justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal Box */}
      <div className="relative w-full max-w-2xl bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden ring-1 ring-slate-900/5 animate-fade-in">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 border-b border-slate-200 bg-slate-50/50">
          <Search className="w-5 h-5 text-slate-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command, module, or search term (e.g. 'Invoices', 'Revenue', 'Inventory')..."
            className="w-full h-14 px-3 bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="p-1 text-slate-400 hover:text-slate-600 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-slate-200 rounded border border-slate-300 ml-2">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2 divide-y divide-slate-100">
          {filtered.length === 0 ? (
            <div className="py-12 text-center">
              <Search className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-700">No matching commands or modules found</p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Try searching for &quot;Sales&quot;, &quot;Revenue&quot;, &quot;Products&quot;, or &quot;AI&quot;
              </p>
            </div>
          ) : (
            Object.entries(grouped).map(([category, items]) => (
              <div key={category} className="py-1">
                <div className="px-3 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  {category}
                </div>
                {items.map((item) => {
                  const currentIndex = globalCounter++
                  const isSelected = selectedIndex === currentIndex
                  const Icon = item.icon
                  return (
                    <div
                      key={item.id}
                      onClick={() => executeCommand(item)}
                      onMouseEnter={() => setSelectedIndex(currentIndex)}
                      className={`flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-teal-50 text-teal-900 font-medium'
                          : 'text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div
                          className={`p-1.5 rounded-md ${
                            isSelected
                              ? 'bg-teal-600 text-white'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          <Icon className="w-4 h-4" />
                        </div>
                        <div className="truncate">
                          <span className="text-xs font-semibold text-slate-900 block truncate">
                            {item.title}
                          </span>
                          {item.description && (
                            <span className="text-[11px] text-slate-500 block truncate">
                              {item.description}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-1 shrink-0 ml-2">
                        {isSelected && (
                          <span className="text-[10px] text-teal-700 font-semibold flex items-center gap-1">
                            <span>Open</span>
                            <ArrowRight className="w-3 h-3" />
                          </span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            ))
          )}
        </div>

        {/* Footer shortcuts helper */}
        <div className="px-4 py-2 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
          <div className="flex items-center gap-3">
            <span>
              <kbd className="font-mono bg-white px-1 py-0.5 rounded border border-slate-200 text-[10px]">↑</kbd>{' '}
              <kbd className="font-mono bg-white px-1 py-0.5 rounded border border-slate-200 text-[10px]">↓</kbd> to navigate
            </span>
            <span>
              <kbd className="font-mono bg-white px-1 py-0.5 rounded border border-slate-200 text-[10px]">↵</kbd> to select
            </span>
          </div>
          <span>ALLADIN Search &bull; Quick Access</span>
        </div>
      </div>
    </div>
  )
}
