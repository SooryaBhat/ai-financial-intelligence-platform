import React, { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { AlertTriangle, ShieldAlert, CheckCircle, Info, History } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { Table, Column } from '@/components/ui/Table'
import { useToast } from '@/hooks/useToast'
import { formatDate } from '@/lib/utils'
import type { AnomalyDetectionResponse, PredictionHistoryItem } from '@/types/ml.types'

export const MlAnomaliesPage: React.FC = () => {
  const toast = useToast()
  const [netAmount, setNetAmount] = useState(12500)
  const [discountPct, setDiscountPct] = useState(5)

  const scanMutation = useMutation({
    mutationFn: (payload: { netAmount: number; discountPct: number }) =>
      mlService.predictAnomaly({ netAmount: payload.netAmount, discountPct: payload.discountPct }),
    onError: (err: any) => toast.error(err?.response?.data?.message || 'Anomaly scan failed'),
    onSuccess: () => refetchHistory(),
  })

  // Load audit history
  const { data: historyData, refetch: refetchHistory } = useQuery({
    queryKey: ['ml-history', 'anomaly'],
    queryFn: () => mlService.getPredictionHistory('anomaly'),
  })
  const historyItems: PredictionHistoryItem[] = historyData || []

  const result: AnomalyDetectionResponse | null = scanMutation.data || null

  const handleScan = (e: React.FormEvent) => {
    e.preventDefault()
    scanMutation.mutate({ netAmount, discountPct })
  }

  const historyColumns: Column<PredictionHistoryItem>[] = [
    { key: 'created_at', header: 'Timestamp', render: (r) => formatDate(r.created_at) },
    {
      key: 'model_version',
      header: 'Model / Algorithm',
      render: (r) => <span className="font-mono text-xs">{r.model_used || r.model_version || 'Isolation Forest'}</span>,
    },
    {
      key: 'predicted_value',
      header: 'Anomaly Score',
      render: (r) => (r.predicted_value != null ? <span className="font-mono">{r.predicted_value.toFixed(4)}</span> : '-'),
    },
    {
      key: 'is_fallback',
      header: 'Inference Status',
      render: (r) =>
        (r.is_fallback || r.output_data?.is_fallback) ? (
          <Badge variant="warning">Statistical IQR</Badge>
        ) : (
          <Badge variant="success">Isolation Forest</Badge>
        ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Transaction Anomaly Inspector"
        description="Scan invoices and commercial transactions for statistical outliers and audit review signals using Isolation Forest ML"
        icon={<AlertTriangle className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Engine</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Anomaly Detection' },
        ]}
      />

      {/* Advisory Banner */}
      <div className="bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 rounded-lg p-3.5 flex items-start gap-2.5 text-xs text-blue-900 dark:text-blue-200">
        <Info className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
        <p>
          <span className="font-bold">Audit Guidance: </span>
          Flagged transactions represent potential statistical anomalies requiring operational or accounting review. An anomaly alert is not proof or confirmation of fraud.
        </p>
      </div>

      {/* Fallback Warning Banner */}
      {result?.is_fallback && (
        <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div className="text-xs text-amber-900 dark:text-amber-200">
            <span className="font-bold">Using Statistical Baseline (IQR / Z-Score): </span>
            {result.warning_message || 'Computed against empirical transaction percentiles.'}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Form Card */}
        <Card>
          <CardHeader>
            <CardTitle>Submit Transaction for Anomaly Audit</CardTitle>
            <CardDescription>Evaluate net amount and discount variance against historical baselines</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleScan} className="space-y-4">
              <Input
                label="Invoice Net Amount"
                type="number"
                value={netAmount}
                onChange={(e) => setNetAmount(Math.max(0, Number(e.target.value)))}
                required
              />
              <Input
                label="Applied Discount (%)"
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={discountPct}
                onChange={(e) => setDiscountPct(Math.max(0, Math.min(100, Number(e.target.value))))}
                required
              />
              <Button variant="primary" type="submit" className="w-full" isLoading={scanMutation.isPending}>
                Inspect Transaction
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Audit Result Card */}
        <Card className="flex flex-col justify-center">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-primary-600" />
              <span>Audit Diagnostic Output</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!result ? (
              <div className="p-8 text-center text-xs text-surface-400">
                Submit transaction parameters to run anomaly detection.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-surface-500">Anomaly Classification</span>
                  <Badge variant={result.is_anomaly ? 'danger' : 'success'} className="text-xs font-bold gap-1">
                    {result.is_anomaly ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
                    {result.is_anomaly ? 'POTENTIAL ANOMALY (FLAGGED FOR REVIEW)' : 'NORMAL TRANSACTION'}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-surface-100 dark:bg-surface-800">
                    <span className="text-[10px] text-surface-400 uppercase font-bold">Severity Rating</span>
                    <p className="text-sm font-bold text-surface-900 dark:text-surface-100">{result.severity}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-surface-100 dark:bg-surface-800">
                    <span className="text-[10px] text-surface-400 uppercase font-bold">Confidence</span>
                    <p className="text-sm font-bold text-surface-900 dark:text-surface-100">
                      {(result.confidence * (result.confidence <= 1 ? 100 : 1)).toFixed(1)}%
                    </p>
                  </div>
                </div>

                {result.anomaly_score != null && (
                  <div className="p-3 rounded-lg bg-surface-100 dark:bg-surface-800 flex justify-between items-center text-xs">
                    <span className="text-surface-500 font-medium">Outlier Score:</span>
                    <span className="font-mono font-bold text-surface-900 dark:text-surface-100">{result.anomaly_score.toFixed(4)}</span>
                  </div>
                )}

                {result.reason && (
                  <div className="p-3.5 rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50/50 dark:bg-rose-950/20 text-xs text-rose-800 dark:text-rose-300">
                    <p className="font-bold mb-1">Diagnostic Reason:</p>
                    <p>{result.reason}</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Audit History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5 text-surface-500" />
            <span>Anomaly Audit History</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {historyItems.length === 0 ? (
            <p className="text-xs text-surface-500 text-center py-6">No previous anomaly scans recorded.</p>
          ) : (
            <Table columns={historyColumns} data={historyItems} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
