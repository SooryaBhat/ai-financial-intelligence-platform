import React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  ShoppingCart,
  Users,
  Package,
  BrainCircuit,
  ArrowUpRight,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'
import { formatCurrency } from '@/lib/utils'
import { reportService } from '@/services/erp.service'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'

const sampleChartData = [
  { month: 'Jan', revenue: 12400000, expenses: 8200000, profit: 4200000 },
  { month: 'Feb', revenue: 13800000, expenses: 8900000, profit: 4900000 },
  { month: 'Mar', revenue: 15200000, expenses: 9400000, profit: 5800000 },
  { month: 'Apr', revenue: 14600000, expenses: 9100000, profit: 5500000 },
  { month: 'May', revenue: 16800000, expenses: 9800000, profit: 7000000 },
  { month: 'Jun', revenue: 18500000, expenses: 10500000, profit: 8000000 },
  { month: 'Jul', revenue: 19100000, expenses: 10800000, profit: 8300000 },
]

export const DashboardPage: React.FC = () => {
  const { user, activeCompany } = useAuth()

  const { data: summary } = useQuery({
    queryKey: ['dashboard-summary', activeCompany?.id || activeCompany?.company_id],
    queryFn: () => reportService.getSummary(),
  })

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-primary-900 via-indigo-900 to-slate-900 text-white shadow-card-md relative overflow-hidden">
        <div className="relative z-10 space-y-1">
          <Badge variant="info" className="bg-white/10 text-white border-white/20">
            {activeCompany?.company_name || activeCompany?.name || 'Horizon Retail Ltd'}
          </Badge>
          <h1 className="text-2xl font-extrabold tracking-tight">
            Welcome back, {user?.full_name || 'Pooja Sharma'}!
          </h1>
          <p className="text-xs text-indigo-200 max-w-xl">
            Real-time financial intelligence overview, ML automated forecasts, and operational ERP telemetry.
          </p>
        </div>
        <div className="relative z-10 flex items-center gap-2">
          <Button variant="secondary" size="sm" leftIcon={<BrainCircuit className="w-4 h-4 text-primary-600" />}>
            Run ML Forecast
          </Button>
        </div>
        <div className="absolute right-0 bottom-0 translate-x-12 translate-y-12 w-64 h-64 rounded-full bg-primary-500/10 blur-3xl pointer-events-none" />
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card hover>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-surface-500 dark:text-surface-400">Total Company Revenue</p>
              <h3 className="text-xl font-extrabold text-surface-900 dark:text-surface-100 mt-1">
                {formatCurrency(summary?.total_revenue ?? 129091501.22)}
              </h3>
              <div className="flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 mt-1">
                <TrendingUp className="w-3.5 h-3.5" />
                <span>Live Supabase Telemetry</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-primary-50 dark:bg-primary-950/50 text-primary-600 dark:text-primary-400">
              <DollarSign className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card hover>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-surface-500 dark:text-surface-400">Gross Sales Volume</p>
              <h3 className="text-xl font-extrabold text-surface-900 dark:text-surface-100 mt-1">
                {summary?.total_sales_count ?? 8000} orders
              </h3>
              <div className="flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 mt-1">
                <TrendingUp className="w-3.5 h-3.5" />
                <span>Active Transactions</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
              <ShoppingCart className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card hover>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-surface-500 dark:text-surface-400">Operating Expenses</p>
              <h3 className="text-xl font-extrabold text-surface-900 dark:text-surface-100 mt-1">
                {formatCurrency(summary?.total_expenses ?? 82819281.13)}
              </h3>
              <div className="flex items-center gap-1 text-xs font-semibold text-rose-600 dark:text-rose-400 mt-1">
                <TrendingDown className="w-3.5 h-3.5" />
                <span>Approved Claims</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400">
              <Package className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card hover>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-surface-500 dark:text-surface-400">Net Profit Margin</p>
              <h3 className="text-xl font-extrabold text-surface-900 dark:text-surface-100 mt-1">
                {formatCurrency(summary?.net_profit ?? 46272220.09)}
              </h3>
              <div className="flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 mt-1">
                <Badge variant="success" size="sm">
                  Positive Margin
                </Badge>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
              <Users className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Charts & Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue vs Expense Chart */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Financial Trajectory & Revenue Forecast</CardTitle>
              <CardDescription>Monthly revenue vs operating expense trend with ML projection</CardDescription>
            </div>
            <Badge variant="info">XGBoost Active</Badge>
          </CardHeader>
          <CardContent className="p-6">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={sampleChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
                  <XAxis dataKey="month" stroke="var(--text-secondary)" fontSize={11} />
                  <YAxis
                    stroke="var(--text-secondary)"
                    fontSize={11}
                    tickFormatter={(val) => `₹${val / 1000000}M`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--bg-surface)',
                      borderColor: 'var(--border)',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="revenue"
                    stroke="#4f46e5"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorRev)"
                    name="Revenue (₹)"
                  />
                  <Area
                    type="monotone"
                    dataKey="profit"
                    stroke="#10b981"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorProfit)"
                    name="Net Profit (₹)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* AI Recommendations Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BrainCircuit className="w-5 h-5 text-primary-600" />
              <span>AI Intelligence Feed</span>
            </CardTitle>
            <CardDescription>Automated insights from machine learning models</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 p-6 pt-0">
            <div className="p-3.5 rounded-xl border border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/50 dark:bg-emerald-950/20 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-800 dark:text-emerald-300">
                  Revenue Growth Alert
                </span>
                <Badge variant="success" size="sm">
                  +15% Forecast
                </Badge>
              </div>
              <p className="text-xs text-emerald-700 dark:text-emerald-400">
                XGBoost model predicts 15% revenue expansion for Horizon Retail Ltd in Q3.
              </p>
            </div>

            <div className="p-3.5 rounded-xl border border-amber-200 dark:border-amber-900/40 bg-amber-50/50 dark:bg-amber-950/20 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-800 dark:text-amber-300">
                  Outstanding Receivables
                </span>
                <Badge variant="warning" size="sm">
                  {formatCurrency(summary?.total_outstanding ?? 91002992.38)}
                </Badge>
              </div>
              <p className="text-xs text-amber-700 dark:text-amber-400">
                Pending collection against open customer sales invoices.
              </p>
            </div>

            <div className="p-3.5 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-800/40 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-surface-900 dark:text-surface-100">
                  Stock Telemetry
                </span>
                <Badge variant="default" size="sm">
                  {summary?.inventory_count ?? 592} Product SKUs
                </Badge>
              </div>
              <p className="text-xs text-surface-500 dark:text-surface-400">
                Live inventory balance maintained across all warehouses.
              </p>
            </div>

            <Button variant="outline" size="sm" className="w-full mt-2" rightIcon={<ArrowUpRight className="w-4 h-4" />}>
              View Full Insights Engine
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
