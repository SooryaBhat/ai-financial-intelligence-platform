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
import { ModelIntelligenceBanner } from '@/components/ml/ModelIntelligenceBanner'
import type { PredictionHistoryItem } from '@/types/ml.types'

const COLORS = ['#0d9488', '#0284c7', '#d97706', '#e11d48', '#6366f1', '#8b5cf6']

export const MlExpensePage: React.FC = () => {
  const toast = useToast()
  const [category, setCategory] = useState('Salaries')
  const [modelType, setModelType] = useState('random_forest')

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
    downloadAnchor.setAttribute('download', `expense_forecast_${category.toLowerCase()}_${modelType}.json`)
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
      render: (r) => <span className="font-mono text-xs">{r.model_used || r.model_version || 'RandomForest'}</span>,
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
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Pipeline 5</span>}
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
                { label: 'Random Forest (Winner, R²=+0.948)', value: 'random_forest' },
                { label: 'XGBoost Regressor', value: 'xgboost' },
                { label: 'Linear Regression Baseline', value: 'linear_regression' },
                { label: 'Recurring Fixed/Variable Forecaster', value: 'recurring' },
              ]}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              leftIcon={<RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />}
            >
              Re-evaluate
            </Button>
            <Button variant="secondary" size="sm" onClick={handleExport} disabled={!expData} leftIcon={<Download className="w-4 h-4" />}>
              Export
            </Button>
          </div>
        }
      />

      {/* Model Intelligence Banner */}
      <ModelIntelligenceBanner
        pipelineTitle="Pipeline 5: Operating Expense Forecasting"
        selectedAlgorithm={expData?.model_name || expData?.model_used || 'Random Forest Expense Forecaster'}
        modelVersion={expData?.model_version || 'expense_prediction_selected.pkl'}
        valMetricLabel="Val WAPE (R² = +0.948)"
        valMetricValue={expData?.metrics?.val_wape_pct ? `${expData.metrics.val_wape_pct}%` : '19.10%'}
        testMetricLabel="Test Set WAPE"
        testMetricValue={expData?.metrics?.test_wape_pct ? `${expData.metrics.test_wape_pct}%` : '19.58%'}
        holdoutMetricLabel="WAPE"
        holdoutMetricValue="18.00%"
        baselineComparison="18.00% vs 25.51% (Naive)"
        isFallback={expData?.is_fallback}
        warningMessage={expData?.warning_message}
      />

      {isLoading ? (
        <Card className="p-12 text-center">
          <Spinner size="lg" className="mx-auto mb-3" />
          <p className="text-sm font-semibold text-slate-900">Calculating Operating Expense Projections...</p>
        </Card>
      ) : isError ? (
        <Card className="p-8 text-center border-rose-200">
          <p className="text-sm font-semibold text-rose-700">Expense Forecasting Failed</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
            Retry
          </Button>
        </Card>
      ) : expData ? (
        <>
          {/* Main Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Projected {category} Expense</span>
                <h3 className="text-2xl font-black text-slate-900 mt-1">
                  {formatCurrency(expData.predicted_expense)}
                </h3>
                <span className="text-xs text-slate-400 mt-1 block">Expected upcoming month burn</span>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Burn Risk Alert</span>
                <h3
                  className={`text-2xl font-black mt-1 ${
                    expData.expense_risk_alert === 'HIGH_ANOMALOUS_EXPENSE'
                      ? 'text-rose-600'
                      : expData.expense_risk_alert === 'ELEVATED'
                      ? 'text-amber-600'
                      : 'text-teal-700'
                  }`}
                >
                  {expData.expense_risk_alert.replace(/_/g, ' ')}
                </h3>
                <span className="text-xs text-slate-400 mt-1 block">Relative to 3-month trailing moving average</span>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Estimated Transaction Count</span>
                <h3 className="text-2xl font-black text-slate-900 mt-1">
                  {expData.predicted_transaction_count} <span className="text-xs font-normal text-slate-500">invoices</span>
                </h3>
                <Badge variant={expData.is_fallback ? 'warning' : 'success'} className="mt-2 text-[10px]">
                  {expData.model_name || expData.model_used}
                </Badge>
              </CardContent>
            </Card>
          </div>

          {/* Breakdown & Audit Trail */}
          {breakdownData.length > 0 && (
            <Card className="bg-white border-slate-200 shadow-xs">
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <BrainCircuit className="w-4 h-4 text-teal-700" />
                  <span>Cost Center Distribution</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={breakdownData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                        {breakdownData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: any) => [formatCurrency(Number(value)), 'Expense']} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Audit History */}
          {historyItems.length > 0 && (
            <Card className="bg-white border-slate-200 shadow-xs">
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <History className="w-4 h-4 text-teal-700" />
                  <span>Audit Trail & Historical Predictions</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table columns={historyColumns} data={historyItems.slice(0, 5)} keyExtractor={(r) => r.id} emptyMessage="No prior predictions recorded" />
              </CardContent>
            </Card>
          )}
        </>
      ) : null}
    </div>
  )
}
