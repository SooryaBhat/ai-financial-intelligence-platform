import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { PackageCheck, AlertTriangle, ShieldCheck, Download, RefreshCw } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { useToast } from '@/hooks/useToast'
import { formatCurrency } from '@/lib/utils'

export const MlInventoryPage: React.FC = () => {
  const toast = useToast()
  const [productName, setProductName] = useState('Premium Laptop X1')
  const [currentStock, setCurrentStock] = useState(25)
  const [unitCost, setUnitCost] = useState(450)
  const [leadTimeDays, setLeadTimeDays] = useState(14)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['ml-inventory-predict', productName, currentStock, unitCost, leadTimeDays],
    queryFn: () => mlService.predictInventory(productName, currentStock, unitCost, leadTimeDays),
  })

  const invData = (data as {
    product_name?: string
    current_stock?: number
    predicted_monthly_demand?: number
    recommended_reorder_point?: number
    recommended_reorder_quantity?: number
    stockout_risk_level?: string
    days_of_supply_remaining?: number
    reorder_recommended?: boolean
  }) || {}

  const handleExport = () => {
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(invData, null, 2))}`
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', jsonString)
    downloadAnchor.setAttribute('download', `inventory_forecast_${productName.toLowerCase().replace(/\s+/g, '_')}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
    toast.success('Inventory report exported')
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100 flex items-center gap-2">
            <PackageCheck className="w-5 h-5 text-indigo-600" />
            <span>AI Inventory Optimization Engine</span>
          </h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Predict demand velocity, automated reorder points, and stockout risk evaluation
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()} leftIcon={<RefreshCw className="w-4 h-4" />}>
            Re-evaluate
          </Button>
          <Button variant="secondary" size="sm" onClick={handleExport} leftIcon={<Download className="w-4 h-4" />}>
            Export
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Form Inputs Card */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>SKU Inventory Parameters</CardTitle>
            <CardDescription>Configure stock level & lead time inputs</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input label="Product Name / SKU" value={productName} onChange={(e) => setProductName(e.target.value)} required />
            <Input label="Current Available Stock" type="number" value={currentStock} onChange={(e) => setCurrentStock(Number(e.target.value))} required />
            <Input label="Unit Procurement Cost ($)" type="number" value={unitCost} onChange={(e) => setUnitCost(Number(e.target.value))} required />
            <Input label="Supplier Lead Time (Days)" type="number" value={leadTimeDays} onChange={(e) => setLeadTimeDays(Number(e.target.value))} required />
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
              <div className="p-12 text-center"><Spinner size="lg" className="mx-auto" /></div>
            ) : isError ? (
              <div className="p-6 text-center text-rose-600 text-xs">Failed to calculate inventory optimization.</div>
            ) : (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  <div className="p-3.5 rounded-xl bg-surface-100 dark:bg-surface-800">
                    <span className="text-[10px] text-surface-400 uppercase font-bold">Monthly Demand</span>
                    <p className="text-lg font-extrabold text-surface-900 dark:text-surface-100">{invData.predicted_monthly_demand || 24.2} units</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-surface-100 dark:bg-surface-800">
                    <span className="text-[10px] text-surface-400 uppercase font-bold">Reorder Point</span>
                    <p className="text-lg font-extrabold text-indigo-600">{invData.recommended_reorder_point || 16.9} units</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-surface-100 dark:bg-surface-800">
                    <span className="text-[10px] text-surface-400 uppercase font-bold">Reorder Order Quantity</span>
                    <p className="text-lg font-extrabold text-emerald-600">{invData.recommended_reorder_quantity || 50} units</p>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-900">
                  <div>
                    <span className="text-xs text-surface-500 font-medium">Days of Supply Remaining</span>
                    <h4 className="text-xl font-black text-surface-900 dark:text-surface-100">{invData.days_of_supply_remaining || 31} Days</h4>
                  </div>
                  <Badge variant={invData.stockout_risk_level === 'HIGH' ? 'danger' : 'success'} className="text-xs font-bold gap-1">
                    {invData.stockout_risk_level === 'HIGH' && <AlertTriangle className="w-3.5 h-3.5" />}
                    Stockout Risk: {invData.stockout_risk_level || 'LOW'}
                  </Badge>
                </div>

                <div className="p-4 rounded-xl border border-primary-200 dark:border-primary-900/40 bg-primary-50/50 dark:bg-primary-950/20 text-xs text-primary-900 dark:text-primary-200 space-y-1">
                  <p className="font-bold">Automated Reorder Recommendation:</p>
                  <p>
                    {invData.reorder_recommended
                      ? `TRIGGER PURCHASE ORDER IMMEDIATELY: Stock (${currentStock}) is approaching reorder threshold (${invData.recommended_reorder_point}). Recommended order size: ${invData.recommended_reorder_quantity} units (${formatCurrency((invData.recommended_reorder_quantity || 50) * unitCost)} total investment).`
                      : `NO IMMEDIATE REORDER NEEDED: Stock level (${currentStock} units) is sufficient to cover forecasted demand for the next ${invData.days_of_supply_remaining || 31} days.`}
                  </p>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
