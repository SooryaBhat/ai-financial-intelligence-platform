import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ShoppingCart, BrainCircuit, RefreshCw, Download, AlertTriangle, History } from 'lucide-react'
import { mlService, productService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { Spinner } from '@/components/ui/Spinner'
import { Table, Column } from '@/components/ui/Table'
import { useToast } from '@/hooks/useToast'
import { formatCurrency, formatDate } from '@/lib/utils'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import type { SalesForecastItem, PredictionHistoryItem } from '@/types/ml.types'

export const MlSalesPage: React.FC = () => {
  const toast = useToast()
  const [entityType, setEntityType] = useState('product')
  const [modelType, setModelType] = useState('xgboost')
  const [monthsAhead, setMonthsAhead] = useState(3)
  const [selectedProductId, setSelectedProductId] = useState<string>('')

  // Load products for dropdown
  const { data: productsData } = useQuery({
    queryKey: ['products-dropdown'],
    queryFn: () => productService.list(),
  })
  const products = productsData?.items || []

  const { data: salesData, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['ml-sales-forecast', entityType, modelType, monthsAhead, selectedProductId],
    queryFn: () =>
      mlService.predictSales({
        entityType,
        modelType,
        monthsAhead,
        entityId: selectedProductId || undefined,
      }),
  })

  // Load audit history
  const { data: historyData } = useQuery({
    queryKey: ['ml-history', 'sales'],
    queryFn: () => mlService.getPredictionHistory('sales'),
  })
  const historyItems: PredictionHistoryItem[] = historyData || []

  const predictions = salesData?.predictions || []

  const handleExport = () => {
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(salesData, null, 2))}`
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', jsonString)
    downloadAnchor.setAttribute('download', `sales_forecast_${entityType}_${modelType}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
    toast.success('Sales forecast exported')
  }

  const columns: Column<SalesForecastItem>[] = [
    { key: 'month', header: 'Forecast Period' },
    { key: 'predicted_units_sold', header: 'Predicted Units', render: (r) => `${r.predicted_units_sold.toLocaleString()} units` },
    { key: 'predicted_sales_amount', header: 'Predicted Revenue', render: (r) => formatCurrency(r.predicted_sales_amount) },
  ]

  const historyColumns: Column<PredictionHistoryItem>[] = [
    { key: 'created_at', header: 'Timestamp', render: (r) => formatDate(r.created_at) },
    {
      key: 'model_version',
      header: 'Model / Algorithm',
      render: (r) => <span className="font-mono text-xs">{r.model_used || r.model_version || 'XGBoost'}</span>,
    },
    {
      key: 'predicted_value',
      header: 'Total Units Projected',
      render: (r) => (r.predicted_value != null ? `${Math.round(r.predicted_value).toLocaleString()} units` : '-'),
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
        title="Sales Demand Forecast"
        description="Predict upcoming product and category unit sales volumes using trained ML models on historical sales records"
        icon={<ShoppingCart className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Engine</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Sales Demand' },
        ]}
        actions={
          <div className="flex items-center gap-2.5 flex-wrap">
            {products.length > 0 && (
              <Select
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
                options={[
                  { label: 'All Products (Aggregated)', value: '' },
                  ...products.map((p) => ({ label: p.name, value: p.id })),
                ]}
              />
            )}
            <Select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              options={[
                { label: 'Product Level', value: 'product' },
                { label: 'Category Level', value: 'category' },
              ]}
            />
            <Select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              options={[
                { label: 'XGBoost Regressor', value: 'xgboost' },
                { label: 'LightGBM Regressor', value: 'lightgbm' },
              ]}
            />
            <Select
              value={monthsAhead.toString()}
              onChange={(e) => setMonthsAhead(Number(e.target.value))}
              options={[
                { label: '3 Months Horizon', value: '3' },
                { label: '6 Months Horizon', value: '6' },
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
            <Button variant="secondary" size="sm" onClick={handleExport} leftIcon={<Download className="w-4 h-4" />}>
              Export
            </Button>
          </div>
        }
      />

      {/* Fallback Warning Banner */}
      {salesData?.is_fallback && (
        <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div className="text-xs text-amber-900 dark:text-amber-200">
            <span className="font-bold">Using Statistical Baseline Estimate: </span>
            {salesData.warning_message || 'Insufficient sales transaction history for reliable machine learning inference. Projections are computed from rolling averages.'}
          </div>
        </div>
      )}

      {isLoading ? (
        <Card className="p-12 text-center">
          <Spinner size="lg" className="mx-auto mb-3" />
          <p className="text-sm font-semibold text-surface-900 dark:text-surface-100">Running Sales Demand Inference...</p>
        </Card>
      ) : isError ? (
        <Card className="p-8 text-center border-danger-200">
          <p className="text-sm font-semibold text-danger-600">Sales Prediction Service Unavailable</p>
          <p className="text-xs text-surface-500 mt-1">Unable to retrieve predictions from the ML service. Ensure sales data is seeded.</p>
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
                <h3 className="text-base font-bold text-surface-900 dark:text-surface-100 mt-1">{salesData?.model_used || 'XGBoost'}</h3>
                <Badge variant={salesData?.is_fallback ? 'warning' : 'info'} className="mt-2">
                  {salesData?.is_fallback ? 'Fallback Mode' : `Target: ${salesData?.entity_type || 'Product'}`}
                </Badge>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 font-medium">Total Predicted Units</p>
                <h3 className="text-xl font-extrabold text-emerald-600 mt-1">
                  {(salesData?.total_predicted_units || 0).toLocaleString()} units
                </h3>
                <p className="text-xs text-surface-400 mt-1">Sum over next {monthsAhead} months</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 font-medium">Total Projected Sales Revenue</p>
                <h3 className="text-xl font-extrabold text-surface-900 dark:text-surface-100 mt-1">
                  {formatCurrency(salesData?.total_predicted_amount || 0)}
                </h3>
                <Badge variant="success" className="mt-2">Forward Projection</Badge>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BrainCircuit className="w-5 h-5 text-emerald-600" />
                <span>Monthly Unit Sales Demand Projection</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              {predictions.length === 0 ? (
                <p className="text-xs text-surface-500 text-center py-8">No forecast data generated.</p>
              ) : (
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={predictions} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
                      <XAxis dataKey="month" stroke="var(--text-secondary)" fontSize={11} />
                      <YAxis stroke="var(--text-secondary)" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border)', borderRadius: '8px', fontSize: '12px' }} />
                      <Bar dataKey="predicted_units_sold" fill="#10b981" radius={[4, 4, 0, 0]} name="Predicted Units" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Forecast Output Table</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table columns={columns} data={predictions} />
            </CardContent>
          </Card>

          {/* Audit History */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="w-5 h-5 text-surface-500" />
                <span>Prediction Audit History</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {historyItems.length === 0 ? (
                <p className="text-xs text-surface-500 text-center py-6">No previous sales forecasts recorded for this company.</p>
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
