import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Layers, BrainCircuit, RefreshCw, Download, AlertTriangle, History } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { Spinner } from '@/components/ui/Spinner'
import { Table, Column } from '@/components/ui/Table'
import { useToast } from '@/hooks/useToast'
import { formatCurrency, formatDate } from '@/lib/utils'
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts'
import type { PredictionHistoryItem } from '@/types/ml.types'

const COLORS = ['#0d9488', '#0284c7', '#d97706', '#e11d48', '#6366f1', '#8b5cf6']

export const MlExpensePage: React.FC = () => {
  const toast = useToast()
  const [category, setCategory] = useState('Salaries')
  const [modelType, setModelType] = useState('xgboost')

  const { data: expData, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['ml-expense-predict', category, modelType],
    queryFn: () => mlService.predictExpense({ category, modelType }),
  })

  // Load audit history
  const { data: historyData } = useQuery({
    queryKey: ['ml-history', 'expense'],
    queryFn: () => mlService.getPredictionHistory('expense'),
  })
  const historyItems: PredictionHistoryItem[] = historyData || []

  const breakdownData = expData?.category_breakdown
    ? Object.entries(expData.category_breakdown).map(([name, value]) => ({ name, value }))
    : []

  const handleExport = () => {
    if (!expData) return
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(expData, null, 2))}`
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', jsonString)
    downloadAnchor.setAttribute('download', `expense_forecast_${category.toLowerCase()}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
    toast.success('Expense forecast exported')
  }

  const historyColumns: Column<PredictionHistoryItem>[] = [
    { key: 'created_at', header: 'Timestamp', render: (r) => formatDate(r.created_at) },
    {
      key: 'model_version',
      header: 'Model / Algorithm',
      render: (r) => <span className="font-mono text-xs">{r.model_used || r.model_version || 'XGBoost'}</span>,
    },
    {
      key: 'predicted_value',
      header: 'Predicted Expense',
      render: (r) => (r.predicted_value != null ? formatCurrency(r.predicted_value) : '-'),
    },
    {
      key: 'is_fallback',
      header: 'Inference Status',
      render: (r) =>
        (r.is_fallback || r.output_data?.is_fallback) ? (
          <Badge variant="warning">Statistical Fallback</Badge>
        ) : (
          <Badge variant="success">ML Inference</Badge>
        ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Operating Expense Forecast"
        description="Forecast future category expenditure, analyze departmental cost centers, and detect surge anomalies"
        icon={<Layers className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Engine</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Expense Forecast' },
        ]}
        actions={
          <div className="flex items-center gap-2.5 flex-wrap">
            <Select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              options={[
                { label: 'Salaries & Payroll', value: 'Salaries' },
                { label: 'Rent & Utilities', value: 'Rent' },
                { label: 'Marketing & Ad Spend', value: 'Marketing' },
                { label: 'IT & Cloud Software', value: 'Software' },
                { label: 'Office Supplies & Ops', value: 'Supplies' },
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
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              leftIcon={<RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />}
            >
              Predict
            </Button>
            <Button variant="secondary" size="sm" onClick={handleExport} disabled={!expData} leftIcon={<Download className="w-4 h-4" />}>
              Export
            </Button>
          </div>
        }
      />

      {/* Fallback Warning Banner */}
      {expData?.is_fallback && (
        <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div className="text-xs text-amber-900 dark:text-amber-200">
            <span className="font-bold">Using Statistical Baseline Estimate: </span>
            {expData.warning_message || 'Insufficient expense vouchers for machine learning inference. Projected from recent expense transaction trends.'}
          </div>
        </div>
      )}

      {isLoading ? (
        <Card className="p-12 text-center">
          <Spinner size="lg" className="mx-auto" />
          <p className="text-xs text-surface-500 mt-2">Computing category expense forecast...</p>
        </Card>
      ) : isError || !expData ? (
        <Card className="p-8 text-center border border-danger-200 rounded-lg">
          <p className="text-sm font-semibold text-danger-600">Expense prediction failed</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
            Retry
          </Button>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 font-medium">Model Used</p>
                <h3 className="text-base font-bold text-surface-900 dark:text-surface-100 mt-1">{expData.model_used || 'XGBoost'}</h3>
                <Badge variant={expData.is_fallback ? 'warning' : 'info'} className="mt-2">
                  Category: {expData.category || category}
                </Badge>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 font-medium">Predicted Category Spend</p>
                <h3 className="text-xl font-extrabold text-surface-900 dark:text-surface-100 mt-1">
                  {formatCurrency(expData.predicted_expense)}
                </h3>
                <p className="text-xs text-surface-400 mt-1">{expData.predicted_transaction_count} expected transactions</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 font-medium">Expense Surge Risk Alert</p>
                <Badge
                  variant={expData.expense_risk_alert === 'NORMAL' ? 'success' : expData.expense_risk_alert === 'MEDIUM' ? 'warning' : 'danger'}
                  className="mt-2 text-sm font-bold uppercase"
                >
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
              {breakdownData.length === 0 ? (
                <p className="text-xs text-surface-500 text-center py-8">No category breakdown records available.</p>
              ) : (
                <div className="h-72 w-full flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={breakdownData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={90}
                        label={(e) => `${e.name}: ${formatCurrency(e.value)}`}
                      >
                        {breakdownData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: unknown) => formatCurrency(Number(value) || 0)} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Audit History */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="w-5 h-5 text-surface-500" />
                <span>Expense Forecast Audit History</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {historyItems.length === 0 ? (
                <p className="text-xs text-surface-500 text-center py-6">No previous expense forecasts recorded.</p>
              ) : (
                <Table columns={historyColumns} data={historyItems} />
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
