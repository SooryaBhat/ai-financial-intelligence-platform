import React from 'react'
import { Link } from 'react-router-dom'
import {
  TrendingUp,
  BrainCircuit,
  Bot,
  Building2,
  Package,
  Receipt,
  ShoppingCart,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Layers,
  LineChart,
  HelpCircle,
  Search,
} from 'lucide-react'
import { AlladinLogo } from '@/components/brand/AlladinLogo'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'

export const LandingPage: React.FC = () => {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen bg-white text-slate-900 flex flex-col selection:bg-teal-500 selection:text-white">
      {/* ── Top Header Navigation ─────────────────────────────────── */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <AlladinLogo size="md" showFullName={false} to="/" />

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <a href="#product" className="hover:text-teal-700 transition-colors">
              Product
            </a>
            <a href="#features" className="hover:text-teal-700 transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-teal-700 transition-colors">
              How It Works
            </a>
            <Link to="/help" className="hover:text-teal-700 transition-colors flex items-center gap-1">
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Help & Docs</span>
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link to="/apps">
                <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Go to Workspace
                </Button>
              </Link>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" size="sm" className="text-slate-700 hover:text-slate-900">
                    Sign In
                  </Button>
                </Link>
                <Link to="/register">
                  <Button variant="primary" size="sm">
                    Get Started
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── Hero Section ─────────────────────────────────────────── */}
      <section className="relative pt-16 pb-20 md:pt-24 md:pb-28 overflow-hidden bg-gradient-to-b from-slate-50/80 via-white to-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center space-y-5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-200/80 text-teal-800 text-xs font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-pulse" />
              <span>Enterprise ERP + Decision Intelligence</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-950 leading-[1.12]">
              Run your business with clarity.{' '}
              <span className="text-teal-700">Make decisions with intelligence.</span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto">
              Manage business operations, forecast what comes next, and understand your company&apos;s
              performance from one intelligent workspace.
            </p>

            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
              {isAuthenticated ? (
                <Link to="/dashboard" className="w-full sm:w-auto">
                  <Button variant="primary" size="lg" className="w-full sm:w-auto shadow-sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                    Open Your Workspace
                  </Button>
                </Link>
              ) : (
                <>
                  <Link to="/register" className="w-full sm:w-auto">
                    <Button variant="primary" size="lg" className="w-full sm:w-auto shadow-sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                      Get Started Free
                    </Button>
                  </Link>
                  <Link to="/login" className="w-full sm:w-auto">
                    <Button variant="outline" size="lg" className="w-full sm:w-auto">
                      Sign In to Account
                    </Button>
                  </Link>
                </>
              )}
            </div>

            <div className="pt-4 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500 font-medium">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-teal-600" /> Multi-Tenant ERP
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-teal-600" /> XGBoost & SARIMA Forecasts
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-teal-600" /> Grounded AI Business Assistant
              </span>
            </div>
          </div>

          {/* ── Realistic Product Dashboard Preview ─────────────────── */}
          <div id="product" className="mt-14 max-w-5xl mx-auto rounded-xl border border-slate-200/90 shadow-xl bg-white overflow-hidden ring-1 ring-slate-900/5">
            {/* Window Top Bar */}
            <div className="bg-slate-100/90 px-4 py-2.5 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-slate-300" />
                <div className="w-3 h-3 rounded-full bg-slate-300" />
                <div className="w-3 h-3 rounded-full bg-slate-300" />
                <span className="ml-3 text-xs font-medium text-slate-600 font-mono">
                  app.alladin.internal / workspace / dashboard
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200/50">
                  Live Telemetry
                </span>
              </div>
            </div>

            {/* Dashboard Mockup Content */}
            <div className="p-5 sm:p-7 bg-slate-50/60 space-y-5">
              {/* Top Bar of Preview */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-teal-700 text-white font-bold flex items-center justify-center text-sm shadow-sm">
                    A
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">ALLADIN Intelligence Workspace</h3>
                    <p className="text-xs text-slate-500">Commercial ERP &bull; Horizon Retail Ltd &bull; FY 2026</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="px-3 py-1 rounded bg-white border border-slate-200 text-xs text-slate-600 flex items-center gap-2">
                    <Search className="w-3.5 h-3.5 text-slate-400" />
                    <span>Search records (⌘K)</span>
                  </div>
                  <div className="px-2.5 py-1 rounded bg-teal-600 text-white text-xs font-medium flex items-center gap-1.5">
                    <Bot className="w-3.5 h-3.5" />
                    <span>AI Copilot Active</span>
                  </div>
                </div>
              </div>

              {/* KPI Strip */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-white p-3.5 rounded-lg border border-slate-200">
                  <span className="text-[11px] font-medium text-slate-500">Total Revenue</span>
                  <p className="text-lg font-bold text-slate-900 mt-0.5">₹129,091,501</p>
                  <span className="text-[10px] font-semibold text-teal-700 flex items-center gap-1 mt-0.5">
                    <TrendingUp className="w-3 h-3" /> Live ERP Audited
                  </span>
                </div>

                <div className="bg-white p-3.5 rounded-lg border border-slate-200">
                  <span className="text-[11px] font-medium text-slate-500">Gross Sales Orders</span>
                  <p className="text-lg font-bold text-slate-900 mt-0.5">8,000 orders</p>
                  <span className="text-[10px] font-semibold text-teal-700 flex items-center gap-1 mt-0.5">
                    <ShoppingCart className="w-3 h-3" /> Across 4 Branches
                  </span>
                </div>

                <div className="bg-white p-3.5 rounded-lg border border-slate-200">
                  <span className="text-[11px] font-medium text-slate-500">Operating Expenses</span>
                  <p className="text-lg font-bold text-slate-900 mt-0.5">₹82,819,281</p>
                  <span className="text-[10px] font-medium text-slate-500 flex items-center gap-1 mt-0.5">
                    <Receipt className="w-3 h-3" /> Within Target Budget
                  </span>
                </div>

                <div className="bg-white p-3.5 rounded-lg border border-slate-200">
                  <span className="text-[11px] font-medium text-slate-500">Net Profit Margin</span>
                  <p className="text-lg font-bold text-slate-900 mt-0.5">₹46,272,220</p>
                  <span className="text-[10px] font-semibold text-teal-700 flex items-center gap-1 mt-0.5">
                    <CheckCircle2 className="w-3 h-3" /> 35.8% Margin Health
                  </span>
                </div>
              </div>

              {/* Main Visual: Two Columns */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Visual Chart Panel */}
                <div className="md:col-span-2 bg-white p-4 rounded-lg border border-slate-200">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">Revenue & Cashflow Projection</h4>
                      <p className="text-[11px] text-slate-500">Actual financial performance vs XGBoost 6-month model</p>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-teal-50 text-teal-700 border border-teal-200 font-semibold">
                      XGBoost Active
                    </span>
                  </div>

                  {/* Simulated SVG Trajectory Chart */}
                  <div className="h-44 w-full bg-slate-50 rounded border border-slate-100 p-3 flex flex-col justify-end">
                    <div className="h-32 w-full flex items-end gap-3 px-2">
                      <div className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-full bg-slate-200 h-16 rounded-t" />
                        <span className="text-[9px] text-slate-400">Jan</span>
                      </div>
                      <div className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-full bg-slate-200 h-20 rounded-t" />
                        <span className="text-[9px] text-slate-400">Feb</span>
                      </div>
                      <div className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-full bg-slate-200 h-22 rounded-t" />
                        <span className="text-[9px] text-slate-400">Mar</span>
                      </div>
                      <div className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-full bg-slate-200 h-24 rounded-t" />
                        <span className="text-[9px] text-slate-400">Apr</span>
                      </div>
                      <div className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-full bg-teal-600 h-28 rounded-t" />
                        <span className="text-[9px] font-semibold text-teal-700">May (Fcst)</span>
                      </div>
                      <div className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-full bg-teal-600 h-30 rounded-t" />
                        <span className="text-[9px] font-semibold text-teal-700">Jun (Fcst)</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* AI Assistant Context Drawer Preview */}
                <div className="bg-white p-4 rounded-lg border border-slate-200 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center gap-2 pb-2.5 border-b border-slate-100">
                      <div className="p-1 rounded bg-teal-50 text-teal-700">
                        <Bot className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-slate-900">ALLADIN AI Assistant</h4>
                        <p className="text-[10px] text-slate-500">Database Grounded</p>
                      </div>
                    </div>

                    <div className="mt-3 space-y-2 text-xs">
                      <div className="p-2 rounded bg-slate-100 text-slate-700">
                        <span className="font-semibold text-[10px] text-slate-500 block mb-0.5">User Prompt</span>
                        &quot;Which product SKUs need replenishment before Q3?&quot;
                      </div>
                      <div className="p-2 rounded bg-teal-50/80 border border-teal-100 text-slate-800">
                        <span className="font-semibold text-[10px] text-teal-700 block mb-0.5">ALLADIN Response</span>
                        Based on warehouse telemetry, 3 items are approaching safety threshold: Premium Laptop X1 (12 units) and 2 cables.
                      </div>
                    </div>
                  </div>

                  <div className="pt-2">
                    <span className="text-[10px] font-medium text-slate-400 block text-center">
                      Connected to real company data &bull; Secure RBAC
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Feature Sections ─────────────────────────────────────── */}
      <section id="features" className="py-20 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16 space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-teal-700">Enterprise Capabilities</h2>
            <p className="text-3xl font-extrabold text-slate-950 tracking-tight">
              An Integrated Architecture Built for Real Businesses
            </p>
            <p className="text-sm text-slate-600">
              Combine your daily operational records with machine-learning forecasts and an intelligent assistant.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Feature 1: ERP Operations */}
            <div className="p-6 rounded-xl border border-slate-200 bg-white hover:border-teal-300 transition-colors space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
                <Building2 className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">ERP & Ledger Management</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Complete operational records covering sales orders, purchase requests, customer invoices,
                suppliers, expenses, and payments with multi-company support.
              </p>
              <ul className="text-xs text-slate-500 space-y-1.5 pt-1">
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>Sales orders & billing</span>
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>Purchases & supplier tracking</span>
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>Expense categories & receipts</span>
                </li>
              </ul>
            </div>

            {/* Feature 2: ML Forecasting */}
            <div className="p-6 rounded-xl border border-slate-200 bg-white hover:border-teal-300 transition-colors space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
                <TrendingUp className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Machine-Learning Forecasting</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Trained statistical and regression models (XGBoost, SARIMA, LightGBM) forecast upcoming
                monthly revenue, sales volume, profit margins, and expense trends.
              </p>
              <ul className="text-xs text-slate-500 space-y-1.5 pt-1">
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>1 to 24-month horizon models</span>
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>Confidence interval bounds</span>
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>Category-level sales predictions</span>
                </li>
              </ul>
            </div>

            {/* Feature 3: Inventory Intelligence */}
            <div className="p-6 rounded-xl border border-slate-200 bg-white hover:border-teal-300 transition-colors space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
                <Package className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Inventory & Stock Telemetry</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Track stock across multiple warehouses, monitor inward and outward stock movements,
                and calculate automated reorder points before shortages occur.
              </p>
              <ul className="text-xs text-slate-500 space-y-1.5 pt-1">
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>Automated safety stock triggers</span>
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>Supplier lead-time calculations</span>
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>Multi-warehouse movements</span>
                </li>
              </ul>
            </div>

            {/* Feature 4: AI Assistant */}
            <div className="p-6 rounded-xl border border-slate-200 bg-white hover:border-teal-300 transition-colors space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
                <Bot className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Persistent AI Business Assistant</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Ask questions about your business in natural language. The assistant draws directly on your
                active company ledger context to provide truthful, grounded answers.
              </p>
              <ul className="text-xs text-slate-500 space-y-1.5 pt-1">
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>Available throughout the app</span>
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>Grounded in company database</span>
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  <span>Pre-configured operational prompts</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── How It Works Section ─────────────────────────────────── */}
      <section id="how-it-works" className="py-20 bg-slate-50/70 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14 space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-teal-700">Workflow</h2>
            <p className="text-3xl font-extrabold text-slate-950 tracking-tight">
              From Business Records to Decision Intelligence
            </p>
            <p className="text-sm text-slate-600">
              Three clear steps to organize your operations and predict what comes next.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-xl border border-slate-200 relative">
              <span className="text-3xl font-black text-teal-700/20 absolute top-4 right-4">01</span>
              <div className="w-9 h-9 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center font-bold mb-3">
                <Layers className="w-4 h-4" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Record Operational Transactions</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Log invoices, sales orders, purchase receipts, expenses, and inventory transactions.
                Each record is structured and tenant-isolated under your company profile.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 relative">
              <span className="text-3xl font-black text-teal-700/20 absolute top-4 right-4">02</span>
              <div className="w-9 h-9 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center font-bold mb-3">
                <LineChart className="w-4 h-4" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Run Machine Learning Models</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Execute predictive models against historical ledger metrics to forecast future revenue,
                detect expense anomalies, evaluate stockout risks, and score business health.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 relative">
              <span className="text-3xl font-black text-teal-700/20 absolute top-4 right-4">03</span>
              <div className="w-9 h-9 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center font-bold mb-3">
                <BrainCircuit className="w-4 h-4" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Act with Decision Intelligence</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Consult the persistent AI assistant for clear summaries, review automated KPI indicators,
                and make operational decisions backed by audited data rather than guesswork.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Ready to Start CTA Banner ────────────────────────────── */}
      <section className="py-16 bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-950 tracking-tight">
            Ready to bring clarity to your business data?
          </h2>
          <p className="text-sm text-slate-600 max-w-xl mx-auto">
            Set up your organization, connect your team, and access the ALLADIN ERP and forecasting platform.
          </p>
          <div className="pt-2 flex items-center justify-center gap-3">
            <Link to="/register">
              <Button variant="primary" size="md" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Create Company Account
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" size="md">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Professional SaaS Footer ──────────────────────────────── */}
      <footer className="bg-slate-50 py-12 border-t border-slate-200 text-slate-600 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div className="space-y-3 md:col-span-1">
              <AlladinLogo size="sm" showFullName={false} to="/" />
              <p className="text-slate-500 text-[11px] leading-relaxed">
                AI-powered Ledger Learning and Analytics for Decision Intelligence Network.
              </p>
              <p className="text-teal-700 font-medium text-[11px]">
                From business data to intelligent decisions.
              </p>
            </div>

            <div>
              <h4 className="font-bold text-slate-900 mb-3 uppercase tracking-wider text-[11px]">Platform</h4>
              <ul className="space-y-2 text-slate-600">
                <li><Link to="/login" className="hover:text-teal-700">Commercial ERP</Link></li>
                <li><Link to="/login" className="hover:text-teal-700">Revenue Forecasting</Link></li>
                <li><Link to="/login" className="hover:text-teal-700">Inventory Telemetry</Link></li>
                <li><Link to="/login" className="hover:text-teal-700">AI Assistant</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-bold text-slate-900 mb-3 uppercase tracking-wider text-[11px]">Documentation</h4>
              <ul className="space-y-2 text-slate-600">
                <li><Link to="/help" className="hover:text-teal-700">User Guide</Link></li>
                <li><Link to="/help" className="hover:text-teal-700">ML Forecast Methodology</Link></li>
                <li><Link to="/help" className="hover:text-teal-700">API Documentation</Link></li>
                <li><Link to="/help" className="hover:text-teal-700">Security & Isolation</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-bold text-slate-900 mb-3 uppercase tracking-wider text-[11px]">Security</h4>
              <p className="text-slate-500 text-[11px] leading-relaxed mb-2">
                Tenant isolation and role-based permissions safeguard your commercial and ledger data.
              </p>
              <div className="flex items-center gap-1.5 text-slate-700 font-medium">
                <ShieldCheck className="w-4 h-4 text-teal-600" />
                <span>Enterprise Encrypted</span>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-slate-500 text-[11px]">
            <p>
              &copy; {new Date().getFullYear()} ALLADIN Platform. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <Link to="/help" className="hover:text-teal-700">Documentation</Link>
              <Link to="/login" className="hover:text-teal-700">Sign In</Link>
              <Link to="/register" className="hover:text-teal-700">Register</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
