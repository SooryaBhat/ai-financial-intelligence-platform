import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { DollarSign, BrainCircuit, Download, RefreshCw, AlertTriangle, History } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { Spinner } from '@/components/ui/Spinner'
import { Table, Column } from '@/components/ui/Table'
import { useToast } from '@/hooks/useToast'
import { formatCurrency, formatDate } from '@/lib/utils'
import type { PredictionHistoryItem } from '@/types/ml.types'

export const MlProfitPage: React.FC = () => {
  const toast = useToast()
  const [projectedRevenueInput, setProjectedRevenueInput] = useState<string>('')

  const revenueNum = projectedRevenueInput ? Number(projectedRevenueInput) : undefined

  const { data: profitData, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['ml-profit-predict', revenueNum],
    queryFn: () => mlService.predictProfit({ projectedRevenue: revenueNum }),
  })

  // Load audit history
  const { data: historyData } = useQuery({
    queryKey: ['ml-history', 'profit'],
    queryFn: () => mlService.getPredictionHistory('profit'),
  })
  const historyItems: PredictionHistoryItem[] = historyData || []

  const handleExport = () => {
    if (!profitData) return
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(profitData, null, 2))}`
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', jsonString)
    downloadAnchor.setAttribute('download', `profit_prediction.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
    toast.success('Profit prediction exported')
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
      header: 'Predicted Profit',
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
        title="Net Profit & Margin Predictor"
        description="Forecast future net operating profits, gross margins, and profitability status based on ledger cashflows"
        icon={<DollarSign className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Engine</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Profit Prediction' },
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
            <Button variant="secondary" size="sm" onClick={handleExport} disabled={!profitData} leftIcon={<Download className="w-4 h-4" />}>
              Export
            </Button>
          </div>
        }
      />

      {/* Fallback Warning Banner */}
      {profitData?.is_fallback && (
        <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div className="text-xs text-amber-900 dark:text-amber-200">
            <span className="font-bold">Using Baseline Financial Estimation: </span>
            {profitData.warning_message || 'Insufficient sales/expense history for non-linear regression. Margins are derived from current ledger actuals.'}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Revenue Baseline Input</CardTitle>
            <CardDescription>Optional manual target or leave blank to derive from historical database sales</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Projected Revenue Target"
              type="number"
              placeholder="Auto-compute from sales history"
              value={projectedRevenueInput}
              onChange={(e) => setProjectedRevenueInput(e.target.value)}
            />
            <p className="text-[11px] text-surface-400">
              When left blank, the ML engine queries the company sales orders and reconciles against recent monthly run-rates.
            </p>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BrainCircuit className="w-5 h-5 text-emerald-600" />
              <span>Profit Forecast & Margin Diagnostics</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {isLoading ? (
              <div className="p-12 text-center">
                <Spinner size="lg" className="mx-auto" />
                <p className="text-xs text-surface-500 mt-2">Computing net profit projection from ledger transactions...</p>
              </div>
            ) : isError || !profitData ? (
              <div className="p-8 text-center border border-danger-200 rounded-lg">
                <p className="text-sm font-semibold text-danger-600">Failed to calculate profit prediction</p>
                <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
                  Retry
                </Button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/50">
                    <span className="text-xs font-semibold text-emerald-800 dark:text-emerald-300">Predicted Net Profit</span>
                    <h3 className="text-xl font-extrabold text-emerald-700 dark:text-emerald-200 mt-1">
                      {formatCurrency(profitData.predicted_profit)}
                    </h3>
                  </div>

                  <div className="p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900/50">
                    <span className="text-xs font-semibold text-indigo-800 dark:text-indigo-300">Profit Margin %</span>
                    <h3 className="text-xl font-extrabold text-indigo-700 dark:text-indigo-200 mt-1">
                      {profitData.predicted_profit_margin_pct.toFixed(2)}%
                    </h3>
                  </div>

                  <div className="p-4 rounded-xl bg-surface-100 dark:bg-surface-800">
                    <span className="text-xs font-semibold text-surface-600 dark:text-surface-400">Confidence Score</span>
                    <h3 className="text-xl font-extrabold text-surface-900 dark:text-surface-100 mt-1">
                      {(profitData.confidence_score * (profitData.confidence_score <= 1 ? 100 : 1)).toFixed(1)}%
                    </h3>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-900">
                  <span className="text-xs font-medium text-surface-700 dark:text-surface-300">Profitability Status Classification:</span>
                  <Badge variant={profitData.profitability_status === 'HEALTHY' || profitData.profitability_status === 'HIGH_MARGIN' ? 'success' : 'warning'} className="text-xs font-bold uppercase">
                    {profitData.profitability_status}
                  </Badge>
                </div>

                {profitData.influencing_factors && Object.keys(profitData.influencing_factors).length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-surface-400 uppercase tracking-wider">Influencing Baseline Factors</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {Object.entries(profitData.influencing_factors).map(([key, value]) => (
                        <div key={key} className="p-2.5 rounded-lg bg-surface-100 dark:bg-surface-800">
                          <span className="text-surface-400 capitalize">{key.replace(/_/g, ' ')}:</span>
                          <p className="font-bold text-surface-900 dark:text-surface-100">
                            {typeof value === 'number' ? (value > 1000 ? formatCurrency(value) : value.toFixed(2)) : String(value)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
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
            <span>Profit Prediction Audit History</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {historyItems.length === 0 ? (
            <p className="text-xs text-surface-500 text-center py-6">No previous profit forecasts recorded.</p>
          ) : (
            <Table columns={historyColumns} data={historyItems} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
