import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  BookOpen,
  TrendingUp,
  Bot,
  Package,
  Command,
  ChevronRight,
  ArrowLeft,
  Search,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { AlladinLogo } from '@/components/brand/AlladinLogo'

export const HelpPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState('getting-started')
  const [searchQuery, setSearchQuery] = useState('')

  const sections = [
    {
      id: 'getting-started',
      title: 'Getting Started',
      icon: BookOpen,
      content: (
        <div className="space-y-4 text-xs text-slate-700 leading-relaxed">
          <h3 className="text-base font-bold text-slate-900">Welcome to ALLADIN</h3>
          <p>
            <strong>ALLADIN</strong> stands for <em>AI-powered Ledger Learning and Analytics for Decision Intelligence Network</em>.
            It provides business operators with a unified workspace that bridges daily transaction operations (ERP)
            with predictive machine-learning telemetry and conversational assistance.
          </p>

          <h4 className="text-sm font-semibold text-slate-900 pt-2">Initial Setup Workflow</h4>
          <ol className="list-decimal pl-5 space-y-2">
            <li>
              <strong>Create Organization:</strong> Navigate to Company settings or complete the onboarding flow to set your currency, fiscal timezone, and branches.
            </li>
            <li>
              <strong>Configure Master Data:</strong> Add your products, catalog SKUs, customer directory, and approved suppliers.
            </li>
            <li>
              <strong>Log Daily Operations:</strong> Generate sales orders and purchase orders. Invoices and payments update your financial ledger in real-time.
            </li>
            <li>
              <strong>Inspect Predictions:</strong> Once transactions are recorded, access the Forecasting tab to view automated revenue, sales, and expense projections.
            </li>
          </ol>
        </div>
      ),
    },
    {
      id: 'erp-modules',
      title: 'ERP Modules & Operations',
      icon: Package,
      content: (
        <div className="space-y-4 text-xs text-slate-700 leading-relaxed">
          <h3 className="text-base font-bold text-slate-900">Core ERP Architecture</h3>
          <p>
            ALLADIN&apos;s ERP modules are structured to follow standard business accounting and supply-chain workflows:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50/50">
              <span className="font-bold text-slate-900 block mb-1">Commercial & Sales</span>
              <p className="text-slate-600">
                Track quotation requests, customer orders, and issue official GST/VAT invoices. Payments reconcile against invoices.
              </p>
            </div>
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50/50">
              <span className="font-bold text-slate-900 block mb-1">Purchases & Suppliers</span>
              <p className="text-slate-600">
                Manage vendor catalog prices, submit purchase orders, and verify warehouse receipt of goods before disbursement.
              </p>
            </div>
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50/50">
              <span className="font-bold text-slate-900 block mb-1">Inventory & Warehouses</span>
              <p className="text-slate-600">
                Multi-location tracking across central hubs and retail branches. Automated reorder warnings flag low safety stock.
              </p>
            </div>
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50/50">
              <span className="font-bold text-slate-900 block mb-1">Expenses & Financials</span>
              <p className="text-slate-600">
                Classify operational expenditure by category (Salaries, Marketing, Rent, Utilities) to feed predictive expense algorithms.
              </p>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'forecasting-ml',
      title: 'Machine-Learning Forecasts',
      icon: TrendingUp,
      content: (
        <div className="space-y-4 text-xs text-slate-700 leading-relaxed">
          <h3 className="text-base font-bold text-slate-900">Predictive Analytics Engine</h3>
          <p>
            ALLADIN incorporates dedicated machine learning models trained on historical transaction records:
          </p>

          <div className="space-y-3 pt-2">
            <div className="border-l-2 border-teal-600 pl-3">
              <span className="font-bold text-slate-900">Revenue Forecasting (XGBoost & SARIMA)</span>
              <p className="text-slate-600 mt-0.5">
                Evaluates seasonality, trend cycles, and past revenue volume to estimate upcoming monthly cash inflows for 1 to 24 months.
              </p>
            </div>

            <div className="border-l-2 border-teal-600 pl-3">
              <span className="font-bold text-slate-900">Inventory Demand & Reorder Trigger</span>
              <p className="text-slate-600 mt-0.5">
                Estimates item run-rate against vendor lead times to calculate the optimal day and quantity for replenishment.
              </p>
            </div>

            <div className="border-l-2 border-teal-600 pl-3">
              <span className="font-bold text-slate-900">Anomaly Detection (Isolation Forest)</span>
              <p className="text-slate-600 mt-0.5">
                Scans invoices and disbursements to flag statistical outliers in discount rates, transaction sizes, or atypical supplier invoices.
              </p>
            </div>

            <div className="border-l-2 border-teal-600 pl-3">
              <span className="font-bold text-slate-900">Business Health Score (Composite KPI Index)</span>
              <p className="text-slate-600 mt-0.5">
                Scores organization performance from 0 to 100 based on revenue growth rate, operating profit margin, expense control, and receivable aging.
              </p>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'ai-assistant',
      title: 'ALLADIN AI Assistant',
      icon: Bot,
      content: (
        <div className="space-y-4 text-xs text-slate-700 leading-relaxed">
          <h3 className="text-base font-bold text-slate-900">Persistent Conversational Copilot</h3>
          <p>
            The assistant is available across every screen in the ALLADIN workspace via the top navigation bar or the persistent action trigger.
          </p>

          <h4 className="text-sm font-semibold text-slate-900 pt-1">Grounding & Tenant Isolation</h4>
          <p>
            Answers generated by the AI assistant are grounded strictly in your authenticated company database.
            It evaluates your actual transactions, current inventory numbers, and recent predictions to provide verifiable business answers.
          </p>

          <div className="bg-teal-50 border border-teal-200 rounded-lg p-3 space-y-1.5">
            <span className="font-bold text-teal-900 block">Recommended Inquiries</span>
            <ul className="list-disc pl-4 space-y-1 text-teal-800">
              <li>&quot;Summarize our gross sales and profit for the past 30 days.&quot;</li>
              <li>&quot;Which inventory items are currently below their reorder threshold?&quot;</li>
              <li>&quot;What are the top three operating expense categories this quarter?&quot;</li>
              <li>&quot;Explain the revenue trajectory projected by the XGBoost model.&quot;</li>
            </ul>
          </div>
        </div>
      ),
    },
    {
      id: 'shortcuts',
      title: 'Keyboard Shortcuts',
      icon: Command,
      content: (
        <div className="space-y-4 text-xs text-slate-700 leading-relaxed">
          <h3 className="text-base font-bold text-slate-900">Quick Navigation & Shortcuts</h3>
          <p>
            Use keyboard shortcuts to rapidly access modules and search throughout your company records:
          </p>

          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="py-2 px-3 font-semibold text-slate-900">Action</th>
                  <th className="py-2 px-3 font-semibold text-slate-900">Shortcut</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="py-2 px-3">Open Global Command Palette & Search</td>
                  <td className="py-2 px-3 font-mono text-teal-700 font-semibold">Ctrl + K / ⌘ + K</td>
                </tr>
                <tr>
                  <td className="py-2 px-3">Open / Close AI Assistant Drawer</td>
                  <td className="py-2 px-3 font-mono text-teal-700 font-semibold">Ctrl + J / ⌘ + J</td>
                </tr>
                <tr>
                  <td className="py-2 px-3">Close Modals or Search Palette</td>
                  <td className="py-2 px-3 font-mono text-teal-700 font-semibold">Escape</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      ),
    },
  ]

  const filteredSections = sections.filter(
    (s) =>
      s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      searchQuery === ''
  )

  const activeContent = sections.find((s) => s.id === activeSection)

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5">
              <ArrowLeft className="w-4 h-4" />
              <span>Back to App</span>
            </Link>
            <div className="h-4 w-px bg-slate-200" />
            <AlladinLogo size="sm" showFullName={false} to="/help" />
          </div>

          <div className="flex items-center gap-2">
            <Link to="/dashboard">
              <Button variant="outline" size="sm">
                Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {/* Banner */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 mb-8 shadow-sm">
          <div className="max-w-2xl">
            <Badge variant="info" className="bg-teal-50 text-teal-800 border-teal-200 mb-2">
              ALLADIN Knowledge Base
            </Badge>
            <h1 className="text-2xl font-extrabold text-slate-950 tracking-tight">
              Documentation & User Guides
            </h1>
            <p className="text-xs text-slate-600 mt-1">
              Comprehensive guidance on ERP operations, predictive models, the conversational assistant, and security.
            </p>
          </div>
        </div>

        {/* 2-Column Docs Layout */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Navigation Sidebar */}
          <div className="space-y-1">
            <div className="relative mb-2 px-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search topics..."
                className="w-full pl-8 pr-2 py-1.5 text-xs bg-white border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-teal-600"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
            </div>
            <div className="px-3 pb-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Navigation
            </div>
            {filteredSections.map((sec) => {
              const Icon = sec.icon
              const isActive = activeSection === sec.id
              return (
                <button
                  key={sec.id}
                  onClick={() => setActiveSection(sec.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-colors text-left ${
                    isActive
                      ? 'bg-teal-50 text-teal-800 font-semibold border border-teal-200/80'
                      : 'text-slate-600 hover:bg-white hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-teal-700' : 'text-slate-400'}`} />
                    <span>{sec.title}</span>
                  </div>
                  {isActive && <ChevronRight className="w-3.5 h-3.5 text-teal-700" />}
                </button>
              )
            })}
          </div>

          {/* Content Area */}
          <div className="md:col-span-3">
            <Card className="bg-white border-slate-200 shadow-sm min-h-[460px]">
              <CardContent className="p-6 sm:p-8">
                {activeContent?.content}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        ALLADIN Platform Knowledge & User Documentation &bull; Built for Enterprise Decision Intelligence
      </footer>
    </div>
  )
}
