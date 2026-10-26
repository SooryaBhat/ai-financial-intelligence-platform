import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { DollarSign, BrainCircuit, Download, RefreshCw, History } from 'lucide-react'
import { mlService } from '@/services/erp.service'
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

export const MlProfitPage: React.FC = () => {
  const toast = useToast()
  const [modelType, setModelType] = useState('lightgbm')
  const [projectedRevenueInput, setProjectedRevenueInput] = useState<string>('')

  const revenueNum = projectedRevenueInput ? Number(projectedRevenueInput) : undefined

  const { data: profitData, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['ml-profit-predict', modelType, revenueNum],
    queryFn: () => mlService.predictProfit({ modelType, projectedRevenue: revenueNum }),
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
    downloadAnchor.setAttribute('download', `profit_prediction_${modelType}.json`)
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
      render: (r) => <span className="font-mono text-xs">{r.model_used || r.model_version || 'LightGBM'}</span>,
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
        title="Net Operating Profit Predictor"
        description="Forecast future net operating profits, gross margins, and profitability status based on ledger cashflows"
        icon={<DollarSign className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Pipeline 4</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Profit Prediction' },
        ]}
        actions={
          <div className="flex items-center gap-2 flex-wrap">
            <Select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              options={[
                { label: 'LightGBM Regressor (Winner, Val WAPE 12.15%)', value: 'lightgbm' },
                { label: 'Random Forest Regressor', value: 'random_forest' },
                { label: 'XGBoost Regressor', value: 'xgboost' },
                { label: 'Linear Regression Baseline', value: 'linear_regression' },
                { label: 'Accounting Identity Margin Bridge', value: 'margin_bridge' },
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
            <Button variant="secondary" size="sm" onClick={handleExport} disabled={!profitData} leftIcon={<Download className="w-4 h-4" />}>
              Export
            </Button>
          </div>
        }
      />

      {/* Model Intelligence Banner */}
      <ModelIntelligenceBanner
        pipelineTitle="Pipeline 4: Net Operating Profit Prediction"
        selectedAlgorithm={profitData?.model_name || profitData?.model_used || 'LightGBM Profit Forecaster'}
        modelVersion={profitData?.model_version || 'profit_prediction_selected.pkl'}
        valMetricLabel="Val WAPE (Volume Error)"
        valMetricValue={profitData?.metrics?.val_wape_pct ? `${profitData.metrics.val_wape_pct}%` : '12.15%'}
        testMetricLabel="Test Set WAPE"
        testMetricValue={profitData?.metrics?.test_wape_pct ? `${profitData.metrics.test_wape_pct}%` : '18.73%'}
        holdoutMetricLabel="WAPE"
        holdoutMetricValue="11.08%"
        baselineComparison="11.08% vs 15.68% (Naive)"
        isFallback={profitData?.is_fallback}
        warningMessage={profitData?.warning_message}
      />

      {/* Revenue Scenario Override Form */}
      <Card className="bg-white border-slate-200 shadow-xs">
        <CardContent className="p-4 flex items-center gap-4 flex-wrap">
          <div className="flex-1 min-w-[240px]">
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Projected Upcoming Monthly Revenue Override (Optional)
            </label>
            <Input
              type="number"
              placeholder="Auto-derived from latest revenue ledger if blank"
              value={projectedRevenueInput}
              onChange={(e) => setProjectedRevenueInput(e.target.value)}
            />
          </div>
          <Button variant="outline" size="sm" className="mt-5" onClick={() => refetch()} disabled={isFetching}>
            Apply Scenario
          </Button>
        </CardContent>
      </Card>

      {isLoading ? (
        <Card className="p-12 text-center">
          <Spinner size="lg" className="mx-auto mb-3" />
          <p className="text-sm font-semibold text-slate-900">Computing Profit Trajectories from General Ledger...</p>
        </Card>
      ) : isError ? (
        <Card className="p-8 text-center border-rose-200">
          <p className="text-sm font-semibold text-rose-700">Profit Prediction Failed</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
            Retry
          </Button>
        </Card>
      ) : profitData ? (
        <>
          {/* Main Output Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Projected Net Monthly Profit</span>
                <h3 className={`text-2xl font-black mt-1 ${profitData.predicted_profit >= 0 ? 'text-teal-700' : 'text-rose-600'}`}>
                  {formatCurrency(profitData.predicted_profit)}
                </h3>
                <span className="text-xs text-slate-400 mt-1 block">Forecasted across operational expenses</span>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Projected Profit Margin</span>
                <h3 className="text-2xl font-black text-slate-900 mt-1">
                  {profitData.predicted_profit_margin_pct.toFixed(1)}%
                </h3>
                <span className="text-xs text-slate-400 mt-1 block">Net Profit / Projected Revenue</span>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-xs">
              <CardContent className="p-5">
                <span className="text-xs font-medium text-slate-500">Profitability Status</span>
                <h3 className="text-lg font-bold text-slate-900 mt-1">{profitData.profitability_status.replace(/_/g, ' ')}</h3>
                <Badge
                  variant={
                    profitData.profitability_status === 'HIGHLY_PROFITABLE'
                      ? 'success'
                      : profitData.profitability_status === 'MODERATELY_PROFITABLE'
                      ? 'info'
                      : 'warning'
                  }
                  className="mt-2 text-[10px]"
                >
                  {profitData.model_name || profitData.model_used}
                </Badge>
              </CardContent>
            </Card>
          </div>

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
