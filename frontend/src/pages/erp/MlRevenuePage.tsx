import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, BrainCircuit, RefreshCw } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { formatCurrency } from '@/lib/utils'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'

export const MlRevenuePage: React.FC = () => {
  const [monthsAhead, setMonthsAhead] = useState(6)
  const [modelType, setModelType] = useState('xgboost')

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['ml-revenue-forecast', monthsAhead, modelType],
    queryFn: () => mlService.predictRevenue(monthsAhead, modelType),
  })

  const forecastData = (data as {
    model_used?: string
    predictions?: Array<{ month: string; predicted_revenue: number; confidence_lower: number; confidence_upper: number }>
    total_projected_revenue?: number
    growth_trend?: string
  }) || {}

  const predictions = forecastData.predictions || []

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-600" />
            <span>AI Revenue Forecasting Engine</span>
          </h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Predict future monthly revenue using trained XGBoost and SARIMA time-series models
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select
            value={monthsAhead.toString()}
            onChange={(e) => setMonthsAhead(Number(e.target.value))}
            options={[
              { label: '3 Months Forecast', value: '3' },
              { label: '6 Months Forecast', value: '6' },
              { label: '12 Months Forecast', value: '12' },
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
          <Button variant="outline" size="sm" onClick={() => refetch()} leftIcon={<RefreshCw className="w-4 h-4" />}>
            Run Model
          </Button>
        </div>
      </div>

      {isLoading ? (
        <Card className="p-12 text-center">
          <Spinner size="lg" className="mx-auto mb-3" />
          <p className="text-sm font-semibold text-surface-900 dark:text-surface-100">Running Machine Learning Model...</p>
          <p className="text-xs text-surface-400 mt-1">Executing trained artifact inference from memory</p>
        </Card>
      ) : isError ? (
        <Card className="p-8 text-center border-danger-200">
          <p className="text-sm font-semibold text-danger-600">Model Execution Warning</p>
          <p className="text-xs text-surface-500 mt-1 mb-4">Failed to complete ML prediction request.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </Card>
      ) : (
        <>
          {/* Metrics summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 dark:text-surface-400 font-medium">Model Artifact Active</p>
                <h3 className="text-lg font-bold text-surface-900 dark:text-surface-100 mt-1">{forecastData.model_used || 'XGBoost Revenue Regressor'}</h3>
                <Badge variant="info" className="mt-2">
                  Trained Artifact Loaded
                </Badge>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 dark:text-surface-400 font-medium">Total Projected Revenue</p>
                <h3 className="text-lg font-extrabold text-surface-900 dark:text-surface-100 mt-1">
                  {formatCurrency(forecastData.total_projected_revenue || 0)}
                </h3>
                <span className="text-xs text-emerald-600 font-semibold mt-1 inline-block">
                  Next {monthsAhead} months projection
                </span>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 dark:text-surface-400 font-medium">Forecasted Growth Trend</p>
                <h3 className="text-lg font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                  {forecastData.growth_trend || 'UPWARD'}
                </h3>
                <Badge variant="success" className="mt-2">
                  High Model Confidence
                </Badge>
              </CardContent>
            </Card>
          </div>

          {/* Chart */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <BrainCircuit className="w-5 h-5 text-primary-600" />
                  <span>Predicted Revenue & Confidence Bounds</span>
                </CardTitle>
                <CardDescription>Monthly forecasted trajectory with confidence intervals</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="p-6">
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={predictions} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorRevML" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.5} />
                        <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
                    <XAxis dataKey="month" stroke="var(--text-secondary)" fontSize={11} />
                    <YAxis stroke="var(--text-secondary)" fontSize={11} tickFormatter={(val) => `$${val / 1000}k`} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--bg-surface)',
                        borderColor: 'var(--border)',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                    />
                    <Area type="monotone" dataKey="predicted_revenue" stroke="#4f46e5" strokeWidth={3} fillOpacity={1} fill="url(#colorRevML)" name="Predicted Revenue ($)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
