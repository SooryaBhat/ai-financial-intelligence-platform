import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Layers, BrainCircuit, RefreshCw, Download } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { useToast } from '@/hooks/useToast'
import { formatCurrency } from '@/lib/utils'
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts'

const COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export const MlExpensePage: React.FC = () => {
  const toast = useToast()
  const [category, setCategory] = useState('Salaries')
  const [modelType, setModelType] = useState('xgboost')

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['ml-expense-predict', category, modelType],
    queryFn: () => mlService.predictExpense(category, modelType),
  })

  const expData = (data as {
    model_used?: string
    category?: string
    predicted_expense?: number
    predicted_transaction_count?: number
    expense_risk_alert?: string
    category_breakdown?: Record<string, number>
  }) || {}

  const breakdownData = Object.entries(expData.category_breakdown || {
    'Salaries & Payroll': 397483.37,
    'Rent & Utilities': 176659.28,
    'Marketing & Growth': 132494.46,
    'IT & Software': 88329.64,
  }).map(([name, value]) => ({ name, value }))

  const handleExport = () => {
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(expData, null, 2))}`
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', jsonString)
    downloadAnchor.setAttribute('download', `expense_forecast_${category.toLowerCase()}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
    toast.success('Expense forecast exported')
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100 flex items-center gap-2">
            <Layers className="w-5 h-5 text-rose-600" />
            <span>AI Expense Predictor & Surge Alert</span>
          </h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Forecast upcoming category spending and detect unusual expenditure surge risks
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            options={[
              { label: 'Salaries & Payroll', value: 'Salaries' },
              { label: 'Rent & Utilities', value: 'Rent' },
              { label: 'Marketing & Ad Spend', value: 'Marketing' },
              { label: 'IT & Cloud Software', value: 'Software' },
            ]}
          />
          <Select
            value={modelType}
            onChange={(e) => setModelType(e.target.value)}
            options={[
              { label: 'XGBoost Regressor', value: 'xgboost' },
              { label: 'Linear Regression', value: 'linear_regression' },
            ]}
          />
          <Button variant="outline" size="sm" onClick={() => refetch()} leftIcon={<RefreshCw className="w-4 h-4" />}>
            Predict
          </Button>
          <Button variant="secondary" size="sm" onClick={handleExport} leftIcon={<Download className="w-4 h-4" />}>
            Export
          </Button>
        </div>
      </div>

      {isLoading ? (
        <Card className="p-12 text-center"><Spinner size="lg" className="mx-auto" /></Card>
      ) : isError ? (
        <Card className="p-8 text-center text-rose-600 text-xs">Expense prediction failed.</Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 font-medium">Model Used</p>
                <h3 className="text-base font-bold text-surface-900 dark:text-surface-100 mt-1">{expData.model_used || 'XGBoost Expense Predictor'}</h3>
                <Badge variant="info" className="mt-2">Category: {expData.category || category}</Badge>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 font-medium">Predicted Category Spend</p>
                <h3 className="text-xl font-extrabold text-surface-900 dark:text-surface-100 mt-1">{formatCurrency(expData.predicted_expense || 883296.38)}</h3>
                <p className="text-xs text-surface-400 mt-1">{expData.predicted_transaction_count || 85} expected transactions</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 font-medium">Expense Surge Risk Alert</p>
                <Badge variant={expData.expense_risk_alert === 'NORMAL' ? 'success' : 'danger'} className="mt-2 text-sm font-bold uppercase">
                  Risk Level: {expData.expense_risk_alert || 'NORMAL'}
                </Badge>
              </CardContent>
            </Card>
          </div>

          {/* Breakdown Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BrainCircuit className="w-5 h-5 text-indigo-600" />
                <span>Forecasted Operating Expense Share</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="h-72 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={breakdownData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={(e) => `${e.name}: $${Math.round(e.value / 1000)}k`}>
                      {breakdownData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: unknown) => formatCurrency(Number(value) || 0)} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
