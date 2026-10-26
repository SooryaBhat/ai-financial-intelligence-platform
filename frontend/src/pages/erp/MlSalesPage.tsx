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
import { ModelIntelligenceBanner } from '@/components/ml/ModelIntelligenceBanner'
import type { SalesForecastItem, PredictionHistoryItem } from '@/types/ml.types'

export const MlSalesPage: React.FC = () => {
  const toast = useToast()
  const [entityType, setEntityType] = useState('product')
  const [modelType, setModelType] = useState('product_profile')
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
      render: (r) => <span className="font-mono text-xs">{r.model_used || r.model_version || 'ProductProfile'}</span>,
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
        description="Predict upcoming product and category unit sales volumes using verified ML models on tenant ledger sales records"
        icon={<ShoppingCart className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Pipeline 2</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Sales Forecast' },
        ]}
        actions={
          <div className="flex items-center gap-2 flex-wrap">
            <Select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              options={[
                { label: 'Product Level', value: 'product' },
                { label: 'Category Level', value: 'category' },
              ]}
            />
            {entityType === 'product' && products.length > 0 && (
              <Select
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
                options={[{ label: 'All Products (Aggregate)', value: '' }, ...products.map((p) => ({ label: p.name, value: p.id }))]}
              />
            )}
            <Select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              options={[
                { label: 'Product Profile (Winner, R²=+0.948)', value: 'product_profile' },
                { label: 'AAGF SKU Forecaster', value: 'aagf' },
                { label: 'LightGBM Regressor', value: 'lightgbm' },
                { label: 'XGBoost Regressor', value: 'xgboost' },
                { label: 'Linear Regression Baseline', value: 'linear_regression' },
              ]}
            />
            <Select
              value={monthsAhead.toString()}
              onChange={(e) => setMonthsAhead(Number(e.target.value))}
              options={[
                { label: '1 Month Ahead', value: '1' },
                { label: '3 Months Ahead', value: '3' },
                { label: '6 Months Ahead', value: '6' },
              ]}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              leftIcon={<RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />}
            >
              Recalculate
            </Button>
            <Button variant="secondary" size="sm" onClick={handleExport} disabled={!salesData} leftIcon={<Download className="w-4 h-4" />}>
              Export
            </Button>
          </div>
        }
      />

      {/* Model Governance Banner */}
      <ModelIntelligenceBanner
        pipelineTitle="Pipeline 2: SKU & Category Sales Demand"
        selectedAlgorithm={salesData?.model_name || salesData?.model_used || 'Product Profile Forecaster'}
        modelVersion={salesData?.model_version || 'sales_forecasting_selected.pkl'}
        valMetricLabel="Val WAPE (R² = +0.948)"
        valMetricValue={salesData?.metrics?.val_wape_pct ? `${salesData.metrics.val_wape_pct}%` : '14.48%'}
        testMetricLabel="Test Set WAPE"
        testMetricValue={salesData?.metrics?.test_wape_pct ? `${salesData.metrics.test_wape_pct}%` : '17.31%'}
        holdoutMetricLabel="WAPE"
        holdoutMetricValue="11.87%"
        baselineComparison="11.87% vs 76.34% (Naive)"
        isFallback={salesData?.is_fallback}
        warningMessage={salesData?.warning_message}
      />

      {isLoading ? (
        <Card className="p-12 text-center">
          <Spinner size="lg" className="mx-auto mb-3" />
          <p className="text-sm font-semibold text-slate-900">Calculating Sales Forecasts...</p>
        </Card>
      ) : isError ? (
        <Card className="p-8 text-center border-rose-200">
          <p className="text-sm font-semibold text-rose-700">Forecast Generation Failed</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
            Retry
          </Button>
        </Card>
      ) : (
        <>
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Total Projected Demand</span>
                <h3 className="text-2xl font-black text-slate-900 mt-1">
                  {Math.round(salesData?.total_predicted_units || 0).toLocaleString()} <span className="text-sm font-medium text-slate-500">units</span>
                </h3>
                <span className="text-xs text-teal-700 font-medium mt-1 inline-block">Over next {monthsAhead} months</span>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Gross Projected Sales Value</span>
                <h3 className="text-2xl font-black text-teal-800 mt-1">
                  {formatCurrency(salesData?.total_predicted_amount || 0)}
                </h3>
                <span className="text-xs text-slate-400 mt-1 inline-block">Estimated at standard retail pricing</span>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Forecasting Algorithm</span>
                <h3 className="text-base font-bold text-slate-900 mt-1">{salesData?.model_name || salesData?.model_used}</h3>
                <Badge variant={salesData?.is_fallback ? 'warning' : 'success'} className="mt-2 text-[10px]">
                  {salesData?.is_fallback ? 'Heuristic Trend' : 'Trained ML Model Active'}
                </Badge>
              </CardContent>
            </Card>
          </div>

          {/* Bar Chart */}
          <Card className="bg-white border-slate-200 shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <BrainCircuit className="w-4 h-4 text-teal-700" />
                  <span>Projected Monthly Volume & Estimated Sales Value</span>
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-6">
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={predictions} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.7} />
                    <XAxis dataKey="month" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderColor: '#e2e8f0',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                      formatter={(val: any, name?: any) => [
                        name === 'Units Sold' ? `${Number(val).toLocaleString()} units` : formatCurrency(Number(val)),
                        name || '',
                      ]}
                    />
                    <Bar dataKey="predicted_units_sold" fill="#0d9488" radius={[4, 4, 0, 0]} name="Units Sold" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Monthly Table Breakdown */}
          <Card className="bg-white border-slate-200 shadow-xs">
            <CardHeader className="border-b border-slate-100 pb-3">
              <CardTitle className="text-sm font-bold text-slate-900">Period-by-Period Forecast Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table columns={columns} data={predictions} keyExtractor={(r) => r.month} emptyMessage="No forecast intervals available" />
            </CardContent>
          </Card>

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
      )}
    </div>
  )
}
