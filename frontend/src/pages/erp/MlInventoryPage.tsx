import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { PackageCheck, AlertTriangle, ShieldCheck, Download, RefreshCw, History } from 'lucide-react'
import { mlService, productService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { Spinner } from '@/components/ui/Spinner'
import { Table, Column } from '@/components/ui/Table'
import { useToast } from '@/hooks/useToast'
import { formatCurrency, formatDate } from '@/lib/utils'
import { ModelIntelligenceBanner } from '@/components/ml/ModelIntelligenceBanner'
import type { PredictionHistoryItem } from '@/types/ml.types'

export const MlInventoryPage: React.FC = () => {
  const toast = useToast()
  const [selectedProductId, setSelectedProductId] = useState<string>('')
  const [productName, setProductName] = useState('Standard Product SKU')
  const [modelType, setModelType] = useState('lightgbm')
  const [currentStock, setCurrentStock] = useState(25)
  const [unitCost, setUnitCost] = useState(450)
  const [leadTimeDays, setLeadTimeDays] = useState(14)

  // Load products from DB
  const { data: productsData } = useQuery({
    queryKey: ['products-list'],
    queryFn: () => productService.list(),
  })
  const products = productsData?.items || []

  // When product is selected, update fields
  const handleProductChange = (prodId: string) => {
    setSelectedProductId(prodId)
    const found = products.find((p) => p.id === prodId)
    if (found) {
      setProductName(found.name)
      if (found.cost_price != null) {
        setUnitCost(Number(found.cost_price))
      }
    }
  }

  // Auto select first product if available and not yet set
  useEffect(() => {
    if (products.length > 0 && !selectedProductId) {
      setSelectedProductId(products[0].id)
      setProductName(products[0].name)
      if (products[0].cost_price != null) {
        setUnitCost(Number(products[0].cost_price))
      }
    }
  }, [productsData?.items, selectedProductId])

  const { data: invData, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['ml-inventory-predict', selectedProductId, productName, modelType, currentStock, unitCost, leadTimeDays],
    queryFn: () =>
      mlService.predictInventory({
        productId: selectedProductId || undefined,
        productName,
        modelType,
        currentStock,
        unitCost,
        leadTimeDays,
      }),
    enabled: !!productName,
  })

  // Load audit history
  const { data: historyData } = useQuery({
    queryKey: ['ml-history', 'inventory'],
    queryFn: () => mlService.getPredictionHistory('inventory'),
  })
  const historyItems: PredictionHistoryItem[] = historyData || []

  const handleExport = () => {
    if (!invData) return
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(invData, null, 2))}`
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', jsonString)
    downloadAnchor.setAttribute('download', `inventory_forecast_${productName.toLowerCase().replace(/\s+/g, '_')}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
    toast.success('Inventory report exported')
  }

  const historyColumns: Column<PredictionHistoryItem>[] = [
    { key: 'created_at', header: 'Timestamp', render: (r) => formatDate(r.created_at) },
    {
      key: 'model_version',
      header: 'Model / Algorithm',
      render: (r) => <span className="font-mono text-xs">{r.model_used || r.model_version || 'LightGBM'}</span>,
    },
    {
      key: 'predicted_value',
      header: 'Monthly Demand Projected',
      render: (r) => (r.predicted_value != null ? `${r.predicted_value.toFixed(1)} units` : '-'),
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
        title="Inventory Optimization & Reorder Predictor"
        description="Predict monthly SKU inventory demand, optimize dynamic reorder points, and protect supply chain continuity"
        icon={<PackageCheck className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Pipeline 3</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Inventory Demand' },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              leftIcon={<RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />}
            >
              Re-evaluate
            </Button>
            <Button variant="secondary" size="sm" onClick={handleExport} disabled={!invData} leftIcon={<Download className="w-4 h-4" />}>
              Export
            </Button>
          </div>
        }
      />

      {/* Model Governance Banner */}
      <ModelIntelligenceBanner
        pipelineTitle="Pipeline 3: Inventory Demand & Reorder Trigger Policy"
        selectedAlgorithm={invData?.model_name || invData?.model_used || 'LightGBM Inventory Forecaster'}
        modelVersion={invData?.model_version || 'inventory_demand_selected.pkl'}
        valMetricLabel="Val WAPE (57.82%)"
        valMetricValue={invData?.metrics?.val_wape_pct ? `${invData.metrics.val_wape_pct}%` : '56.88%'}
        testMetricLabel="Test Set WAPE"
        testMetricValue={invData?.metrics?.test_wape_pct ? `${invData.metrics.test_wape_pct}%` : '58.19%'}
        holdoutMetricLabel="WAPE"
        holdoutMetricValue="53.70%"
        baselineComparison="58.19% vs 79.36% (Demand History Lag 1)"
        isFallback={invData?.is_fallback}
        warningMessage={invData?.warning_message}
      />

      {/* Product & Parameter Selection Form */}
      <Card className="bg-white border-slate-200 shadow-xs">
        <CardHeader className="pb-3 border-b border-slate-100">
          <CardTitle className="text-sm font-bold text-slate-900">Inventory Simulation & Parameter Controls</CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Select SKU and algorithm to simulate dynamic lead time and reorder thresholds
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Target Product SKU</label>
              {products.length > 0 ? (
                <Select
                  value={selectedProductId}
                  onChange={(e) => handleProductChange(e.target.value)}
                  options={products.map((p) => ({ label: p.name, value: p.id }))}
                />
              ) : (
                <Input value={productName} onChange={(e) => setProductName(e.target.value)} placeholder="Product Name" />
              )}
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Forecasting Model</label>
              <Select
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                options={[
                  { label: 'LightGBM (Winner, 100% Service)', value: 'lightgbm' },
                  { label: 'XGBoost Regressor', value: 'xgboost' },
                  { label: 'Random Forest Regressor', value: 'random_forest' },
                  { label: 'Censored Demand Forecaster', value: 'censored' },
                ]}
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Current Stock Level</label>
              <Input type="number" value={currentStock} onChange={(e) => setCurrentStock(Math.max(0, Number(e.target.value)))} />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Unit Cost Price (₹)</label>
              <Input type="number" value={unitCost} onChange={(e) => setUnitCost(Math.max(0, Number(e.target.value)))} />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Supplier Lead Time (Days)</label>
              <Input type="number" value={leadTimeDays} onChange={(e) => setLeadTimeDays(Math.max(1, Number(e.target.value)))} />
            </div>
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <Card className="p-12 text-center">
          <Spinner size="lg" className="mx-auto mb-3" />
          <p className="text-sm font-semibold text-slate-900">Simulating Lead Times & Demand Forecasts...</p>
        </Card>
      ) : isError ? (
        <Card className="p-8 text-center border-rose-200">
          <p className="text-sm font-semibold text-rose-700">Optimization Calculation Failed</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
            Retry
          </Button>
        </Card>
      ) : invData ? (
        <>
          {/* Reorder Recommendation Banner */}
          <div
            className={`p-4 rounded-xl border flex items-center justify-between flex-wrap gap-4 ${
              invData.reorder_recommended ? 'bg-rose-50 border-rose-200 text-rose-900' : 'bg-teal-50 border-teal-200 text-teal-900'
            }`}
          >
            <div className="flex items-center gap-3">
              {invData.reorder_recommended ? (
                <AlertTriangle className="w-6 h-6 text-rose-600 shrink-0" />
              ) : (
                <ShieldCheck className="w-6 h-6 text-teal-600 shrink-0" />
              )}
              <div>
                <h4 className="text-sm font-extrabold">
                  {invData.reorder_recommended
                    ? `Purchase Order Trigger: Reorder ${Math.round(invData.recommended_reorder_quantity)} Units Immediately`
                    : 'Inventory Position Healthy: Stock Level Above Reorder Threshold'}
                </h4>
                <p className="text-xs opacity-90 mt-0.5">
                  Current stock ({invData.current_stock} units) vs Reorder Trigger Point ({invData.recommended_reorder_point} units)
                </p>
              </div>
            </div>
            <Badge variant={invData.stockout_risk_level === 'CRITICAL' ? 'danger' : invData.stockout_risk_level === 'HIGH' ? 'warning' : 'success'}>
              {invData.stockout_risk_level} RISK
            </Badge>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Projected Monthly Demand</span>
                <h3 className="text-2xl font-black text-slate-900 mt-1">
                  {invData.predicted_monthly_demand} <span className="text-xs font-normal text-slate-500">units/mo</span>
                </h3>
                <span className="text-xs text-slate-400 mt-1 block">Daily velocity: {(invData.predicted_monthly_demand / 30).toFixed(1)} units/day</span>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Days of Supply Remaining</span>
                <h3 className={`text-2xl font-black mt-1 ${invData.days_of_supply_remaining < 14 ? 'text-rose-600' : 'text-teal-700'}`}>
                  {invData.days_of_supply_remaining.toFixed(1)} <span className="text-xs font-normal text-slate-500">days</span>
                </h3>
                <span className="text-xs text-slate-400 mt-1 block">Lead time requirement: {leadTimeDays} days</span>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Recommended Reorder Point</span>
                <h3 className="text-2xl font-black text-slate-900 mt-1">
                  {invData.recommended_reorder_point} <span className="text-xs font-normal text-slate-500">units</span>
                </h3>
                <span className="text-xs text-slate-400 mt-1 block">Safety buffer + lead time demand</span>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Optimal Order Quantity (EOQ)</span>
                <h3 className="text-2xl font-black text-teal-800 mt-1">
                  {invData.recommended_reorder_quantity} <span className="text-xs font-normal text-slate-500">units</span>
                </h3>
                <span className="text-xs text-slate-400 mt-1 block">Est. PO Capital: {formatCurrency(invData.recommended_reorder_quantity * unitCost)}</span>
              </CardContent>
            </Card>
          </div>

          {/* Audit Trail */}
          {historyItems.length > 0 && (
            <Card className="bg-white border-slate-200 shadow-xs">
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <History className="w-4 h-4 text-teal-700" />
                  <span>Audit Trail & Historical Forecasts</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table columns={historyColumns} data={historyItems.slice(0, 5)} keyExtractor={(r) => r.id} emptyMessage="No prior recommendations recorded" />
              </CardContent>
            </Card>
          )}
        </>
      ) : null}
    </div>
  )
}
