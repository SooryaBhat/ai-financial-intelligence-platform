import React, { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { AlertTriangle, ShieldAlert, CheckCircle, Info, History } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { Table, Column } from '@/components/ui/Table'
import { useToast } from '@/hooks/useToast'
import { formatDate } from '@/lib/utils'
import { ModelIntelligenceBanner } from '@/components/ml/ModelIntelligenceBanner'
import type { AnomalyDetectionResponse, PredictionHistoryItem } from '@/types/ml.types'

export const MlAnomaliesPage: React.FC = () => {
  const toast = useToast()
  const [modelType, setModelType] = useState('rule_based')
  const [netAmount, setNetAmount] = useState(12500)
  const [discountPct, setDiscountPct] = useState(5)

  const scanMutation = useMutation({
    mutationFn: (payload: { netAmount: number; discountPct: number; modelType: string }) =>
      mlService.predictAnomaly({ netAmount: payload.netAmount, discountPct: payload.discountPct, modelType: payload.modelType }),
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
    scanMutation.mutate({ netAmount, discountPct, modelType })
  }

  const historyColumns: Column<PredictionHistoryItem>[] = [
    { key: 'created_at', header: 'Timestamp', render: (r) => formatDate(r.created_at) },
    {
      key: 'model_version',
      header: 'Model / Algorithm',
      render: (r) => <span className="font-mono text-xs">{r.model_used || r.model_version || 'RuleBased'}</span>,
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
          <Badge variant="success">ML Inference</Badge>
        ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Transaction Anomaly Inspector"
        description="Scan invoices and commercial transactions for statistical outliers and audit review signals using verified ML models"
        icon={<AlertTriangle className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Pipeline 7</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Anomaly Detection' },
        ]}
      />

      {/* Model Governance Banner */}
      <ModelIntelligenceBanner
        pipelineTitle="Pipeline 7: Transaction Anomaly & Outlier Detection"
        selectedAlgorithm={result?.model_name || result?.model_used || 'Rule-Based Anomaly Detector'}
        modelVersion={result?.model_version || 'anomaly_detection_selected.pkl'}
        valMetricLabel="Dev Val F1 (0% FPR)"
        valMetricValue={result?.metrics?.val_f1_score ? `${result.metrics.val_f1_score}` : '0.6667'}
        testMetricLabel="Test Set F1"
        testMetricValue={result?.metrics?.test_f1_score ? `${result.metrics.test_f1_score}` : '0.8947'}
        holdoutMetricLabel="F1"
        holdoutMetricValue="0.6379"
        baselineComparison="F1: 0.895 (0.00% False Positive Rate)"
        isFallback={result?.is_fallback}
        warningMessage={result?.warning_message}
      />

      {/* Advisory Banner */}
      <div className="bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 rounded-lg p-3.5 flex items-start gap-2.5 text-xs text-blue-900 dark:text-blue-200">
        <Info className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
        <p>
          <span className="font-bold">Audit Guidance & Benchmark Note: </span>
          Synthetic threshold evaluation produces high precision on extreme outliers, but misses subtle non-threshold patterns. On the independent Multi-Type Benchmark v2, multivariate PCA and Isolation Forest detect contextual discounts, off-hours spikes, and margin erosion. An anomaly alert is an analytical signal requiring human verification, not confirmation of fraud.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Form Card */}
        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="border-b border-slate-100 pb-3">
            <CardTitle className="text-sm font-bold text-slate-900">Simulate Transaction & Evaluate Risk</CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Input invoice transaction parameters to test anomaly classification
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5">
            <form onSubmit={handleScan} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Anomaly Detection Algorithm</label>
                <Select
                  value={modelType}
                  onChange={(e) => setModelType(e.target.value)}
                  options={[
                    { label: 'Rule-Based Detector (Winner, F1: 0.895, 0% FPR)', value: 'rule_based' },
                    { label: 'Isolation Forest (Unsupervised ML)', value: 'isolation_forest' },
                    { label: 'Robust MAD Anomaly Detector', value: 'robust_mad' },
                    { label: 'PCA Reconstruction Error Detector', value: 'pca' },
                  ]}
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Net Invoice Amount (₹)</label>
                <Input type="number" value={netAmount} onChange={(e) => setNetAmount(Number(e.target.value))} required />
                <span className="text-[11px] text-slate-400 mt-1 block">Standard retail average: ₹15,000 - ₹35,000</span>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Discount Applied (%)</label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={discountPct}
                  onChange={(e) => setDiscountPct(Number(e.target.value))}
                  required
                />
                <span className="text-[11px] text-slate-400 mt-1 block">Discounts exceeding 35% trigger automatic scrutiny</span>
              </div>

              <Button type="submit" variant="primary" className="w-full mt-2" disabled={scanMutation.isPending}>
                {scanMutation.isPending ? 'Executing Anomaly Pipeline...' : 'Run Anomaly Detection Scan'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Results Card */}
        <Card className="bg-white border-slate-200 shadow-xs flex flex-col justify-between">
          <CardHeader className="border-b border-slate-100 pb-3">
            <CardTitle className="text-sm font-bold text-slate-900">Inference Classification Output</CardTitle>
          </CardHeader>
          <CardContent className="p-5 flex-1 flex flex-col justify-center">
            {result ? (
              <div className="space-y-4 text-center">
                <div className="inline-flex p-3 rounded-full bg-slate-50 border border-slate-200 mx-auto">
                  {result.is_anomaly ? (
                    <ShieldAlert className="w-10 h-10 text-rose-600" />
                  ) : (
                    <CheckCircle className="w-10 h-10 text-teal-600" />
                  )}
                </div>

                <div>
                  <h3 className={`text-xl font-black ${result.is_anomaly ? 'text-rose-600' : 'text-teal-700'}`}>
                    {result.is_anomaly ? 'ANOMALOUS TRANSACTION DETECTED' : 'NORMAL TRANSACTION VERIFIED'}
                  </h3>
                  <div className="flex items-center justify-center gap-2 mt-2">
                    <Badge variant={result.is_anomaly ? 'danger' : 'success'}>{result.severity} SEVERITY</Badge>
                    <span className="text-xs font-semibold text-slate-600">
                      Confidence: {result.confidence.toFixed(1)}%
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-left text-xs space-y-1.5">
                  <p className="font-semibold text-slate-700">Diagnostic Details:</p>
                  <p className="text-slate-600">{result.reason}</p>
                  <p className="text-[11px] text-slate-400 font-mono mt-1">
                    Algorithm: {result.model_name || result.model_used} | Score: {result.anomaly_score.toFixed(4)}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center text-slate-400 py-12">
                <AlertTriangle className="w-10 h-10 mx-auto mb-2 opacity-30" />
                <p className="text-sm font-medium">No transaction evaluated yet</p>
                <p className="text-xs mt-1">Fill out the invoice parameters and run the scan above</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Audit History */}
      {historyItems.length > 0 && (
        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="border-b border-slate-100 pb-3">
            <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <History className="w-4 h-4 text-teal-700" />
              <span>Audit Trail & Historical Scans</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table columns={historyColumns} data={historyItems.slice(0, 5)} keyExtractor={(r) => r.id} emptyMessage="No prior scans recorded" />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
