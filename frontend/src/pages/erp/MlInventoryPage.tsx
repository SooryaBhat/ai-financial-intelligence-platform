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
import type { PredictionHistoryItem } from '@/types/ml.types'

export const MlInventoryPage: React.FC = () => {
  const toast = useToast()
  const [selectedProductId, setSelectedProductId] = useState<string>('')
  const [productName, setProductName] = useState('Standard Product SKU')
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
    queryKey: ['ml-inventory-predict', selectedProductId, productName, currentStock, unitCost, leadTimeDays],
    queryFn: () =>
      mlService.predictInventory({
        productId: selectedProductId || undefined,
        productName,
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
      render: (r) => <span className="font-mono text-xs">{r.model_used || r.model_version || 'Inventory ML'}</span>,
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
        title="Inventory Reorder & Replenishment Intelligence"
        description="Predict monthly SKU demand velocity, automated safety stock levels, and stockout risk evaluation"
        icon={<PackageCheck className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Engine</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Inventory Reorder' },
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

      {/* Fallback Warning Banner */}
      {invData?.is_fallback && (
        <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div className="text-xs text-amber-900 dark:text-amber-200">
            <span className="font-bold">Using Statistical Baseline Estimate: </span>
            {invData.warning_message || 'Insufficient historical stock movement records. Safety stock and reorder point computed using deterministic lead-time formulas.'}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Form Inputs Card */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>SKU Inventory Parameters</CardTitle>
            <CardDescription>Select product or configure stock level & lead time inputs</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {products.length > 0 && (
              <div>
                <label className="text-xs font-semibold text-surface-700 dark:text-surface-300 mb-1 block">
                  Select Product from Catalog
                </label>
                <Select
                  value={selectedProductId}
                  onChange={(e) => handleProductChange(e.target.value)}
                  options={[
                    { label: '-- Custom Entry --', value: '' },
                    ...products.map((p) => ({ label: `${p.name} (SKU: ${p.sku})`, value: p.id })),
                  ]}
                />
              </div>
            )}
            <Input label="Product Name / SKU" value={productName} onChange={(e) => setProductName(e.target.value)} required />
            <Input label="Current Available Stock" type="number" value={currentStock} onChange={(e) => setCurrentStock(Math.max(0, Number(e.target.value)))} required />
            <Input label="Unit Procurement Cost" type="number" value={unitCost} onChange={(e) => setUnitCost(Math.max(0, Number(e.target.value)))} required />
            <Input label="Supplier Lead Time (Days)" type="number" value={leadTimeDays} onChange={(e) => setLeadTimeDays(Math.max(1, Number(e.target.value)))} required />
          </CardContent>
        </Card>

        {/* Prediction Results Card */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              <span>AI Stock Optimization Output</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {isLoading ? (
              <div className="p-12 text-center">
                <Spinner size="lg" className="mx-auto" />
                <p className="text-xs text-surface-500 mt-2">Computing optimal safety stock and reorder points...</p>
              </div>
            ) : isError || !invData ? (
              <div className="p-8 text-center border border-danger-200 rounded-lg">
                <p className="text-sm font-semibold text-danger-600">Failed to calculate inventory optimization</p>
                <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
                  Retry
                </Button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  <div className="p-3.5 rounded-xl bg-surface-100 dark:bg-surface-800">
                    <span className="text-[10px] text-surface-400 uppercase font-bold">Monthly Demand</span>
                    <p className="text-lg font-extrabold text-surface-900 dark:text-surface-100">
                      {invData.predicted_monthly_demand.toFixed(1)} units
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-surface-100 dark:bg-surface-800">
                    <span className="text-[10px] text-surface-400 uppercase font-bold">Reorder Point</span>
                    <p className="text-lg font-extrabold text-indigo-600">
                      {invData.recommended_reorder_point.toFixed(1)} units
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-surface-100 dark:bg-surface-800">
                    <span className="text-[10px] text-surface-400 uppercase font-bold">Recommended Order Qty</span>
                    <p className="text-lg font-extrabold text-emerald-600">
                      {Math.round(invData.recommended_reorder_quantity)} units
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-900">
                  <div>
                    <span className="text-xs text-surface-500 font-medium">Days of Supply Remaining</span>
                    <h4 className="text-xl font-black text-surface-900 dark:text-surface-100">
                      {invData.days_of_supply_remaining.toFixed(0)} Days
                    </h4>
                  </div>
                  <Badge variant={invData.stockout_risk_level === 'HIGH' ? 'danger' : invData.stockout_risk_level === 'MEDIUM' ? 'warning' : 'success'} className="text-xs font-bold gap-1">
                    {invData.stockout_risk_level === 'HIGH' && <AlertTriangle className="w-3.5 h-3.5" />}
                    Stockout Risk: {invData.stockout_risk_level}
                  </Badge>
                </div>

                <div className={`p-4 rounded-xl border ${
                  invData.reorder_recommended
                    ? 'border-amber-300 dark:border-amber-900 bg-amber-50/50 dark:bg-amber-950/20 text-amber-900 dark:text-amber-200'
                    : 'border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/50 dark:bg-emerald-950/20 text-emerald-900 dark:text-emerald-200'
                } text-xs space-y-1`}>
                  <p className="font-bold">Automated Reorder Recommendation:</p>
                  <p>
                    {invData.reorder_recommended
                      ? `TRIGGER PURCHASE ORDER: Current stock (${currentStock} units) is below or approaching the reorder threshold (${invData.recommended_reorder_point.toFixed(1)} units). Recommended replenishment order: ${Math.round(invData.recommended_reorder_quantity)} units (${formatCurrency(Math.round(invData.recommended_reorder_quantity) * unitCost)} estimated investment).`
                      : `STOCK HEALTHY: Current stock level (${currentStock} units) is above the safety threshold. Available inventory covers approximately ${invData.days_of_supply_remaining.toFixed(0)} days of forecasted demand.`}
                  </p>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Audit History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5 text-surface-500" />
            <span>Inventory Prediction Audit History</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {historyItems.length === 0 ? (
            <p className="text-xs text-surface-500 text-center py-6">No previous inventory reorder evaluations recorded.</p>
          ) : (
            <Table columns={historyColumns} data={historyItems} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
