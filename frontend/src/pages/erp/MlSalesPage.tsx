import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ShoppingCart, BrainCircuit, RefreshCw, Download } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { Table, Column } from '@/components/ui/Table'
import { useToast } from '@/hooks/useToast'
import { formatCurrency } from '@/lib/utils'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'

interface SalesPredictionItem {
  month: string
  predicted_units_sold: number
  predicted_sales_amount: number
}

export const MlSalesPage: React.FC = () => {
  const toast = useToast()
  const [entityType, setEntityType] = useState('product')
  const [modelType, setModelType] = useState('xgboost')
  const [monthsAhead, setMonthsAhead] = useState(3)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['ml-sales-forecast', entityType, modelType, monthsAhead],
    queryFn: () => mlService.predictSales(entityType, modelType, monthsAhead),
  })

  const salesData = (data as {
    model_used?: string
    entity_type?: string
    predictions?: SalesPredictionItem[]
    total_predicted_units?: number
    total_predicted_amount?: number
  }) || {}

  const predictions = salesData.predictions || []

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

  const columns: Column<SalesPredictionItem>[] = [
    { key: 'month', header: 'Forecast Period' },
    { key: 'predicted_units_sold', header: 'Predicted Units', render: (r) => `${r.predicted_units_sold} units` },
    { key: 'predicted_sales_amount', header: 'Predicted Revenue', render: (r) => formatCurrency(r.predicted_sales_amount) },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100 flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-emerald-600" />
            <span>AI Sales Demand Predictor</span>
          </h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Predict upcoming product and category unit sales volumes using XGBoost or LightGBM
          </p>
        </div>
        <div className="flex items-center gap-3">
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
          <Button variant="outline" size="sm" onClick={() => refetch()} leftIcon={<RefreshCw className="w-4 h-4" />}>
            Predict
          </Button>
          <Button variant="secondary" size="sm" onClick={handleExport} leftIcon={<Download className="w-4 h-4" />}>
            Export
          </Button>
        </div>
      </div>

      {isLoading ? (
        <Card className="p-12 text-center">
          <Spinner size="lg" className="mx-auto mb-3" />
          <p className="text-sm font-semibold text-surface-900 dark:text-surface-100">Running Sales Demand Inference...</p>
        </Card>
      ) : isError ? (
        <Card className="p-8 text-center border-danger-200">
          <p className="text-sm font-semibold text-danger-600">Sales Prediction Error</p>
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
                <h3 className="text-base font-bold text-surface-900 dark:text-surface-100 mt-1">{salesData.model_used || 'XGBoost Sales Predictor'}</h3>
                <Badge variant="info" className="mt-2">Entity: {salesData.entity_type || 'Product'}</Badge>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 font-medium">Total Predicted Units</p>
                <h3 className="text-xl font-extrabold text-emerald-600 mt-1">{salesData.total_predicted_units || 0} units</h3>
                <p className="text-xs text-surface-400 mt-1">Sum over next {monthsAhead} months</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-surface-500 font-medium">Total Projected Sales Revenue</p>
                <h3 className="text-xl font-extrabold text-surface-900 dark:text-surface-100 mt-1">{formatCurrency(salesData.total_predicted_amount || 0)}</h3>
                <Badge variant="success" className="mt-2">High Demand Pace</Badge>
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
        </>
      )}
    </div>
  )
}
