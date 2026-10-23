import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  TrendingUp,
  DollarSign,
  ShoppingCart,
  Package,
  BrainCircuit,
  ArrowRight,
  ArrowUpRight,
  Receipt,
  Bot,
  RefreshCw,
  LayoutGrid,
  AlertCircle,
  Clock,
  Sparkles,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { useAuth } from '@/hooks/useAuth'
import { formatCurrency } from '@/lib/utils'
import { mlService, reportService } from '@/services/erp.service'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const { user, activeCompany, activeBranchId } = useAuth()

  const companyId = activeCompany?.company_id || activeCompany?.id

  // 1. Live ledger summary from database
  const { data: summary, isLoading: isSummaryLoading, refetch: refetchSummary } = useQuery({
    queryKey: ['dashboard-summary', companyId, activeBranchId],
    queryFn: () => reportService.getSummary(activeBranchId || undefined),
    enabled: !!companyId,
  })

  // 2. Machine-learning revenue trajectory backed by database
  const { data: revenueForecast, isLoading: isForecastLoading, refetch: refetchForecast } = useQuery({
    queryKey: ['dashboard-ml-forecast', companyId, activeBranchId],
    queryFn: () => mlService.predictRevenue({ monthsAhead: 6, branchId: activeBranchId || undefined }),
    enabled: !!companyId,
  })

  const handleRefresh = () => {
    refetchSummary()
    refetchForecast()
  }

  // Build chart points from predictions
  const predictions = revenueForecast?.predictions || []
  const chartData = predictions.map((p) => ({
    month: p.month ? p.month.slice(5) : 'Mo',
    revenue: p.predicted_revenue,
    confidence_lower: p.confidence_lower,
    confidence_upper: p.confidence_upper,
  }))

  const recentSales = summary?.recent_sales || []

  return (
    <div className="space-y-6">
      {/* ── Top Header Banner ── */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="default" className="bg-teal-50 text-teal-800 border-teal-200 font-semibold">
              {activeCompany?.company_name || 'Active Workspace'}
            </Badge>
            {activeBranchId && (
              <Badge variant="outline" className="text-slate-600 border-slate-300 font-medium">
                Outlet Filter Active
              </Badge>
            )}
            <span className="text-[11px] text-slate-400 font-medium">Enterprise ERP &bull; Database Backed</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-950 tracking-tight">
            Welcome back, {user?.full_name || 'Workspace Administrator'}
          </h1>
          <p className="text-xs text-slate-500 max-w-2xl">
            Live ledger aggregates, inventory velocity, and verified ML prediction telemetry for your business.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <Link to="/apps">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<LayoutGrid className="w-3.5 h-3.5 text-teal-700" />}
            >
              Apps Launcher
            </Button>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>
          <Link to="/ml/revenue">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<BrainCircuit className="w-4 h-4 text-teal-200" />}
            >
              Run ML Forecast
            </Button>
          </Link>
        </div>
      </div>

      {/* ── Quick Operational Actions Bar ── */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mr-1 shrink-0">
          Quick Actions:
        </span>
        <Link
          to="/invoices"
          className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:border-teal-500 hover:text-teal-800 transition-colors font-medium flex items-center gap-1.5 shadow-2xs whitespace-nowrap"
        >
          <Receipt className="w-3.5 h-3.5 text-teal-700" />
          <span>Invoices</span>
        </Link>
        <Link
          to="/sales"
          className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:border-teal-500 hover:text-teal-800 transition-colors font-medium flex items-center gap-1.5 shadow-2xs whitespace-nowrap"
        >
          <ShoppingCart className="w-3.5 h-3.5 text-teal-700" />
          <span>New Sales Order</span>
        </Link>
        <Link
          to="/products"
          className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:border-teal-500 hover:text-teal-800 transition-colors font-medium flex items-center gap-1.5 shadow-2xs whitespace-nowrap"
        >
          <Package className="w-3.5 h-3.5 text-teal-700" />
          <span>Add Product SKU</span>
        </Link>
        <Link
          to="/expenses"
          className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:border-teal-500 hover:text-teal-800 transition-colors font-medium flex items-center gap-1.5 shadow-2xs whitespace-nowrap"
        >
          <DollarSign className="w-3.5 h-3.5 text-teal-700" />
          <span>Log Expense</span>
        </Link>
        <Link
          to="/ml/chat"
          className="px-3 py-1.5 rounded-lg border border-teal-200 bg-teal-50 text-teal-800 hover:bg-teal-100 transition-colors font-semibold flex items-center gap-1.5 shadow-2xs whitespace-nowrap"
        >
          <Bot className="w-3.5 h-3.5 text-teal-700" />
          <span>Ask AI Assistant</span>
        </Link>
      </div>

      {/* ── 4 Core Real Database KPI Summary Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Total Revenue */}
        <div
          onClick={() => navigate('/sales')}
          className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs hover:border-teal-300 hover:shadow-xs transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Gross Sales Revenue</span>
            <div className="p-2 rounded-lg bg-teal-50 text-teal-700 group-hover:bg-teal-600 group-hover:text-white transition-colors">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            {isSummaryLoading ? (
              <Skeleton className="h-7 w-28" />
            ) : (
              <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
                {formatCurrency(summary?.total_revenue ?? 0)}
              </h3>
            )}
            <div className="flex items-center justify-between mt-2 text-[11px]">
              <span className="text-teal-700 font-semibold flex items-center gap-1">
                <TrendingUp className="w-3 h-3" /> Live Ledger Total
              </span>
              <span className="text-slate-400 group-hover:text-teal-700 transition-colors flex items-center">
                View &rarr;
              </span>
            </div>
          </div>
        </div>

        {/* KPI 2: Sales Volume */}
        <div
          onClick={() => navigate('/sales')}
          className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs hover:border-teal-300 hover:shadow-xs transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Sales Transactions</span>
            <div className="p-2 rounded-lg bg-teal-50 text-teal-700 group-hover:bg-teal-600 group-hover:text-white transition-colors">
              <ShoppingCart className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            {isSummaryLoading ? (
              <Skeleton className="h-7 w-28" />
            ) : (
              <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
                {summary?.total_sales_count ?? 0} orders
              </h3>
            )}
            <div className="flex items-center justify-between mt-2 text-[11px]">
              <span className="text-slate-500 font-medium">Completed Transactions</span>
              <span className="text-slate-400 group-hover:text-teal-700 transition-colors flex items-center">
                View &rarr;
              </span>
            </div>
          </div>
        </div>

        {/* KPI 3: Operating Expenses */}
        <div
          onClick={() => navigate('/expenses')}
          className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs hover:border-teal-300 hover:shadow-xs transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Operating Expenses</span>
            <div className="p-2 rounded-lg bg-slate-100 text-slate-700 group-hover:bg-slate-800 group-hover:text-white transition-colors">
              <Receipt className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            {isSummaryLoading ? (
              <Skeleton className="h-7 w-28" />
            ) : (
              <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
                {formatCurrency(summary?.total_expenses ?? 0)}
              </h3>
            )}
            <div className="flex items-center justify-between mt-2 text-[11px]">
              <span className="text-slate-500 font-medium">Approved Ledger Vouchers</span>
              <span className="text-slate-400 group-hover:text-slate-700 transition-colors flex items-center">
                View &rarr;
              </span>
            </div>
          </div>
        </div>

        {/* KPI 4: Net Profit */}
        <div
          onClick={() => navigate('/ml/profit')}
          className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs hover:border-teal-300 hover:shadow-xs transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Net Operating Profit</span>
            <div className="p-2 rounded-lg bg-teal-50 text-teal-700 group-hover:bg-teal-600 group-hover:text-white transition-colors">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            {isSummaryLoading ? (
              <Skeleton className="h-7 w-28" />
            ) : (
              <h3 className={`text-xl font-extrabold tracking-tight ${(summary?.net_profit ?? 0) >= 0 ? 'text-teal-900' : 'text-rose-700'}`}>
                {formatCurrency(summary?.net_profit ?? 0)}
              </h3>
            )}
            <div className="flex items-center justify-between mt-2 text-[11px]">
              <span className="text-teal-700 font-semibold">Revenue minus Expenses</span>
              <span className="text-slate-400 group-hover:text-teal-700 transition-colors flex items-center">
                Forecast &rarr;
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Main Charts & Intelligence Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ML Trajectory Area Chart */}
        <Card className="lg:col-span-2 bg-white border-slate-200 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-slate-100">
            <div>
              <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-teal-700" />
                <span>Revenue Trajectory & Machine Learning Forecast</span>
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                6-month projection generated via {revenueForecast?.model_used || 'XGBoost Forecaster'}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {revenueForecast?.is_fallback ? (
                <Badge variant="warning" size="sm" className="bg-amber-50 text-amber-800 border-amber-200">
                  Initial Baseline
                </Badge>
              ) : (
                <span className="text-[10px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                  Live DB Trained
                </span>
              )}
              <Link to="/ml/revenue" className="text-xs text-slate-500 hover:text-teal-700">
                <ArrowUpRight className="w-4 h-4" />
              </Link>
            </div>
          </CardHeader>
          <CardContent className="p-5">
            {isForecastLoading ? (
              <div className="h-72 flex items-center justify-center">
                <Skeleton className="h-60 w-full" />
              </div>
            ) : chartData.length > 0 ? (
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="alladinRev" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0d9488" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.7} />
                    <XAxis dataKey="month" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderColor: '#e2e8f0',
                        borderRadius: '8px',
                        fontSize: '12px',
                        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.08)',
                      }}
                      formatter={(val: any) => [formatCurrency(Number(val)), 'Projected Revenue']}
                    />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      stroke="#0d9488"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#alladinRev)"
                      name="Projected Revenue"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-72 flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-200 rounded-lg">
                <Clock className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-sm font-semibold text-slate-700">No Historical Sales Yet</p>
                <p className="text-xs text-slate-400 mt-1 max-w-sm">
                  Add sales orders to start generating machine-learning financial projections for your company.
                </p>
                <Link to="/sales" className="mt-3">
                  <Button size="sm" variant="outline">
                    Create First Sale
                  </Button>
                </Link>
              </div>
            )}
            <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-teal-600" />
                  <span>ML Projected Monthly Revenue</span>
                </span>
                <span className="text-[11px] text-teal-700 font-semibold">
                  Trend: {revenueForecast?.growth_trend || 'STABLE'}
                </span>
              </div>
              <span className="text-[11px] text-slate-400">
                {revenueForecast?.warning_message || 'Model verified against authorized ledger records'}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Operational Intelligence & Alerts Panel */}
        <Card className="bg-white border-slate-200 shadow-xs flex flex-col justify-between">
          <CardHeader className="pb-2 border-b border-slate-100">
            <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-teal-700" />
              <span>Operational Telemetry</span>
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Live status from business modules
            </CardDescription>
          </CardHeader>

          <CardContent className="p-5 space-y-3.5 flex-1">
            {/* Inventory alert */}
            <div
              onClick={() => navigate('/inventory')}
              className="p-3 rounded-lg border border-slate-200 hover:border-teal-400 bg-slate-50 hover:bg-white transition-all cursor-pointer group space-y-1"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">Inventory Status</span>
                <Badge variant="default" size="sm" className="bg-teal-50 text-teal-800 border-teal-200">
                  {summary?.inventory_count ?? 0} SKUs
                </Badge>
              </div>
              <p className="text-[11px] text-slate-600">
                {(summary?.low_stock_count ?? 0) > 0 ? (
                  <span className="text-amber-700 font-semibold flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                    {summary?.low_stock_count} item(s) below reorder safety threshold.
                  </span>
                ) : (
                  'All warehouse safety stocks within parameters.'
                )}
              </p>
            </div>

            {/* Receivables alert */}
            <div
              onClick={() => navigate('/invoices')}
              className="p-3 rounded-lg border border-slate-200 hover:border-teal-400 bg-slate-50 hover:bg-white transition-all cursor-pointer group space-y-1"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">Outstanding Receivables</span>
                <span className="text-xs font-bold text-slate-800">
                  {formatCurrency(summary?.total_outstanding ?? 0)}
                </span>
              </div>
              <p className="text-[11px] text-slate-600">
                Unsettled balance across active customer sales invoices.
              </p>
            </div>

            {/* ML Growth Insight */}
            <div
              onClick={() => navigate('/ml/business-health')}
              className="p-3 rounded-lg border border-teal-200 bg-teal-50/60 hover:bg-teal-50 transition-colors cursor-pointer space-y-1"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-teal-900">Business Health Score</span>
                <Badge variant="success" size="sm">
                  Active
                </Badge>
              </div>
              <p className="text-[11px] text-teal-800 leading-relaxed">
                Evaluates revenue growth, profit margin, expense control, and turnover velocity.
              </p>
            </div>
          </CardContent>

          <div className="p-4 pt-0">
            <Link to="/ml/chat" className="block">
              <Button
                variant="outline"
                size="sm"
                className="w-full text-slate-700 hover:text-teal-800 border-slate-200"
                rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
              >
                Consult AI Copilot
              </Button>
            </Link>
          </div>
        </Card>
      </div>

      {/* ── Recent Sales Ledger Table ── */}
      <Card className="bg-white border-slate-200 shadow-xs">
        <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Clock className="w-4 h-4 text-teal-700" />
              <span>Recent Sales Orders</span>
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Latest commercial orders recorded in the company ledger
            </CardDescription>
          </div>
          <Link to="/sales">
            <Button variant="ghost" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
              View All Sales
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          {recentSales.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase font-bold text-[10px] border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-4">Order #</th>
                    <th className="py-2.5 px-4">Customer</th>
                    <th className="py-2.5 px-4">Date</th>
                    <th className="py-2.5 px-4">Status</th>
                    <th className="py-2.5 px-4 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentSales.map((sale: any) => (
                    <tr key={sale.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-2.5 px-4 font-semibold text-slate-900">{sale.sale_number}</td>
                      <td className="py-2.5 px-4 text-slate-600">{sale.customers?.name || 'Walk-in Customer'}</td>
                      <td className="py-2.5 px-4 text-slate-500">{sale.sale_date}</td>
                      <td className="py-2.5 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          sale.status === 'delivered' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                          sale.status === 'confirmed' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                          'bg-slate-100 text-slate-700'
                        }`}>
                          {sale.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-right font-bold text-slate-900">
                        {formatCurrency(Number(sale.total_amount))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-400">
              <ShoppingCart className="w-8 h-8 mx-auto mb-2 text-slate-300" />
              <p className="text-xs font-semibold text-slate-600">No Sales Orders Found</p>
              <p className="text-[11px] text-slate-400 mt-0.5">Recorded orders will automatically stream into this ledger.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
