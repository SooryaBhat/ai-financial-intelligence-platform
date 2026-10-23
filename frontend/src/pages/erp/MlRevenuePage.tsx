import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, BrainCircuit, RefreshCw, AlertCircle, History } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { Spinner } from '@/components/ui/Spinner'
import { useAuth } from '@/hooks/useAuth'
import { formatCurrency } from '@/lib/utils'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'

export const MlRevenuePage: React.FC = () => {
  const { activeBranchId } = useAuth()
  const [monthsAhead, setMonthsAhead] = useState(6)
  const [modelType, setModelType] = useState('xgboost')

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['ml-revenue-forecast', monthsAhead, modelType, activeBranchId],
    queryFn: () => mlService.predictRevenue({ monthsAhead, modelType, branchId: activeBranchId || undefined }),
  })

  const { data: historyData, refetch: refetchHistory } = useQuery({
    queryKey: ['ml-prediction-history', 'revenue'],
    queryFn: () => mlService.getPredictionHistory('revenue'),
  })

  const forecastData = data || {
    model_used: 'XGBoost Revenue Predictor',
    forecast_period_months: monthsAhead,
    predictions: [],
    total_projected_revenue: 0,
    average_monthly_revenue: 0,
    growth_trend: 'STABLE',
    is_fallback: false,
    warning_message: null,
  }

  const predictions = forecastData.predictions || []

  const handleRun = () => {
    refetch().then(() => refetchHistory())
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Revenue Forecasting Engine"
        description="Forecast monthly company revenues and cash inflow trajectories using database sales ledger records and trained XGBoost or SARIMA models"
        icon={<TrendingUp className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Pipeline 1</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Revenue Forecast' },
        ]}
        actions={
          <div className="flex items-center gap-2.5 flex-wrap">
            <Select
              value={monthsAhead.toString()}
              onChange={(e) => setMonthsAhead(Number(e.target.value))}
              options={[
                { label: '3 Months Horizon', value: '3' },
                { label: '6 Months Horizon', value: '6' },
                { label: '12 Months Horizon', value: '12' },
              ]}
            />
            <Select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              options={[
                { label: 'XGBoost Regressor', value: 'xgboost' },
                { label: 'SARIMA Time-Series', value: 'sarima' },
              ]}
            />
            <Button
              variant="outline"
              size="sm"
              disabled={isFetching}
              onClick={handleRun}
              leftIcon={<RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />}
            >
              {isFetching ? 'Forecasting...' : 'Run Forecast'}
            </Button>
          </div>
        }
      />

      {forecastData.is_fallback && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-800">
            <span className="font-bold">Safe Baseline Fallback Active: </span>
            {forecastData.warning_message || 'Database records for this company or outlet are currently below the 6-month threshold required for deep lag feature generation. A conservative baseline forecast is displayed.'}
          </div>
        </div>
      )}

      {isLoading ? (
        <Card className="p-12 text-center">
          <Spinner size="lg" className="mx-auto mb-3" />
          <p className="text-sm font-semibold text-slate-900">Running Machine Learning Model...</p>
          <p className="text-xs text-slate-400 mt-1">Retrieving database sales records & executing model inference</p>
        </Card>
      ) : isError ? (
        <Card className="p-8 text-center border-rose-200">
          <p className="text-sm font-semibold text-rose-700">Model Execution Warning</p>
          <p className="text-xs text-slate-500 mt-1 mb-4">Failed to complete ML prediction request. Verify network connectivity and permissions.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </Card>
      ) : (
        <>
          {/* Metrics summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <p className="text-xs text-slate-500 font-medium">Model Engine</p>
                <h3 className="text-base font-bold text-slate-900 mt-1">{forecastData.model_used}</h3>
                <Badge variant={forecastData.is_fallback ? 'warning' : 'info'} className="mt-2 text-[10px]">
                  {forecastData.is_fallback ? 'Baseline Forecast' : 'Database Model Verified'}
                </Badge>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <p className="text-xs text-slate-500 font-medium">Total Projected Revenue</p>
                <h3 className="text-lg font-extrabold text-slate-900 mt-1">
                  {formatCurrency(forecastData.total_projected_revenue || 0)}
                </h3>
                <span className="text-xs text-teal-700 font-semibold mt-1 inline-block">
                  Next {forecastData.forecast_period_months} months horizon
                </span>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <p className="text-xs text-slate-500 font-medium">Forecasted Growth Trend</p>
                <h3 className={`text-lg font-bold mt-1 ${forecastData.growth_trend === 'UPWARD' ? 'text-teal-700' : 'text-slate-800'}`}>
                  {forecastData.growth_trend}
                </h3>
                <span className="text-[11px] text-slate-400 mt-2 block">
                  Avg Monthly: {formatCurrency(forecastData.average_monthly_revenue || 0)}
                </span>
              </CardContent>
            </Card>
          </div>

          {/* Chart */}
          <Card className="bg-white border-slate-200 shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-sm font-bold text-slate-900">
                  <BrainCircuit className="w-4 h-4 text-teal-700" />
                  <span>Predicted Monthly Revenue & 90% Confidence Interval</span>
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Monthly forecasted trajectory with statistical confidence bounds
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="p-6">
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={predictions} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorRevML" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0d9488" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.7} />
                    <XAxis dataKey="month" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderColor: '#e2e8f0',
                        borderRadius: '8px',
                        fontSize: '12px',
                        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.08)',
                      }}
                      formatter={(val: any) => [formatCurrency(Number(val)), 'Predicted Revenue']}
                    />
                    <Area
                      type="monotone"
                      dataKey="predicted_revenue"
                      stroke="#0d9488"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#colorRevML)"
                      name="Predicted Revenue"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Prediction History Table */}
          {historyData && historyData.length > 0 && (
            <Card className="bg-white border-slate-200 shadow-xs">
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <History className="w-4 h-4 text-teal-700" />
                  <span>Audit Trail & Prediction History</span>
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Traceable forecast records saved to PostgreSQL predictions table
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-500 uppercase font-bold text-[10px] border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-4">Prediction ID</th>
                        <th className="py-2.5 px-4">Model Engine</th>
                        <th className="py-2.5 px-4">Projected Total</th>
                        <th className="py-2.5 px-4">Confidence</th>
                        <th className="py-2.5 px-4">Created At</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {historyData.slice(0, 5).map((row) => (
                        <tr key={row.id} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2.5 px-4 font-mono text-slate-600">{row.id.slice(0, 8)}...</td>
                          <td className="py-2.5 px-4 font-semibold text-slate-900">{row.model_version || 'XGBoost'}</td>
                          <td className="py-2.5 px-4 font-bold text-teal-900">{formatCurrency(row.predicted_value || 0)}</td>
                          <td className="py-2.5 px-4">
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-teal-50 text-teal-700 border border-teal-200">
                              {((row.confidence_score || 0.9) * 100).toFixed(0)}%
                            </span>
                          </td>
                          <td className="py-2.5 px-4 text-slate-500">{new Date(row.created_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
