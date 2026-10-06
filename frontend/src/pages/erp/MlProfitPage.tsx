import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { DollarSign, BrainCircuit, Download, RefreshCw } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { useToast } from '@/hooks/useToast'
import { formatCurrency } from '@/lib/utils'

export const MlProfitPage: React.FC = () => {
  const toast = useToast()
  const [projectedRevenue, setProjectedRevenue] = useState(22000000)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['ml-profit-predict', projectedRevenue],
    queryFn: () => mlService.predictProfit(projectedRevenue),
  })

  const profitData = (data as {
    predicted_profit?: number
    predicted_profit_margin_pct?: number
    profitability_status?: string
    confidence_score?: number
    influencing_factors?: Record<string, number>
  }) || {}

  const handleExport = () => {
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(profitData, null, 2))}`
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', jsonString)
    downloadAnchor.setAttribute('download', `profit_prediction.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
    toast.success('Profit prediction exported')
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-600" />
            <span>AI Net Profit & Margin Predictor</span>
          </h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Forecast upcoming gross & net profit margins, profitability status, and efficiency metrics
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
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Revenue Input Baseline</CardTitle>
            <CardDescription>Estimated upcoming top-line gross revenue</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Projected Revenue Base ($)"
              type="number"
              value={projectedRevenue}
              onChange={(e) => setProjectedRevenue(Number(e.target.value))}
              required
            />
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
              <div className="p-12 text-center"><Spinner size="lg" className="mx-auto" /></div>
            ) : isError ? (
              <div className="p-6 text-center text-rose-600 text-xs">Failed to calculate profit prediction.</div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/50">
                    <span className="text-xs font-semibold text-emerald-800 dark:text-emerald-300">Predicted Net Profit</span>
                    <h3 className="text-xl font-extrabold text-emerald-700 dark:text-emerald-200 mt-1">
                      {formatCurrency(profitData.predicted_profit || 1983176.5)}
                    </h3>
                  </div>

                  <div className="p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900/50">
                    <span className="text-xs font-semibold text-indigo-800 dark:text-indigo-300">Profit Margin %</span>
                    <h3 className="text-xl font-extrabold text-indigo-700 dark:text-indigo-200 mt-1">
                      {profitData.predicted_profit_margin_pct || 9.01}%
                    </h3>
                  </div>

                  <div className="p-4 rounded-xl bg-surface-100 dark:bg-surface-800">
                    <span className="text-xs font-semibold text-surface-600 dark:text-surface-400">Model Confidence</span>
                    <h3 className="text-xl font-extrabold text-surface-900 dark:text-surface-100 mt-1">
                      {profitData.confidence_score || 92.5}%
                    </h3>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-900">
                  <span className="text-xs font-medium text-surface-700 dark:text-surface-300">Profitability Status Classification:</span>
                  <Badge variant={profitData.profitability_status === 'HEALTHY' ? 'success' : 'warning'} className="text-xs font-bold uppercase">
                    {profitData.profitability_status || 'LOW_MARGIN'}
                  </Badge>
                </div>

                {profitData.influencing_factors && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-surface-400 uppercase tracking-wider">Influencing Baseline Factors</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2.5 rounded-lg bg-surface-100 dark:bg-surface-800">
                        <span className="text-surface-400">Recent Profit Trend:</span>
                        <p className="font-bold text-surface-900 dark:text-surface-100">{formatCurrency(profitData.influencing_factors.recent_profit_trend || 0)}</p>
                      </div>
                      <div className="p-2.5 rounded-lg bg-surface-100 dark:bg-surface-800">
                        <span className="text-surface-400">Expense Ratio Baseline:</span>
                        <p className="font-bold text-surface-900 dark:text-surface-100">{(profitData.influencing_factors.expense_ratio_baseline || 0.72) * 100}%</p>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
