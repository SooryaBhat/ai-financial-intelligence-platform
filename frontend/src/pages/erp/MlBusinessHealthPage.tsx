import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { HeartPulse, ShieldCheck, CheckCircle2, RefreshCw, AlertTriangle, History, Info } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { Table, Column } from '@/components/ui/Table'
import { formatDate } from '@/lib/utils'
import type { PredictionHistoryItem } from '@/types/ml.types'

export const MlBusinessHealthPage: React.FC = () => {
  const { data: healthData, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['ml-business-health'],
    queryFn: () => mlService.predictBusinessHealth({}),
  })

  // Load audit history
  const { data: historyData } = useQuery({
    queryKey: ['ml-history', 'business_health'],
    queryFn: () => mlService.getPredictionHistory('business_health'),
  })
  const historyItems: PredictionHistoryItem[] = historyData || []

  const historyColumns: Column<PredictionHistoryItem>[] = [
    { key: 'created_at', header: 'Timestamp', render: (r) => formatDate(r.created_at) },
    {
      key: 'model_version',
      header: 'Model / Algorithm',
      render: (r) => <span className="font-mono text-xs">{r.model_used || r.model_version || 'Health Scoring'}</span>,
    },
    {
      key: 'predicted_value',
      header: 'Health Score',
      render: (r) => (r.predicted_value != null ? <span className="font-bold">{r.predicted_value.toFixed(1)} / 100</span> : '-'),
    },
    {
      key: 'is_fallback',
      header: 'Inference Status',
      render: (r) =>
        (r.is_fallback || r.output_data?.is_fallback) ? (
          <Badge variant="warning">Baseline Heuristic</Badge>
        ) : (
          <Badge variant="success">ML Scored</Badge>
        ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Business Health Score & Risk Evaluator"
        description="Composite financial health index (0–100), operational grade, liquidity rating, and ML advisory recommendations"
        icon={<HeartPulse className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Engine</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Business Health' },
        ]}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            leftIcon={<RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />}
          >
            Re-evaluate
          </Button>
        }
      />

      {/* Advisory Disclaimer */}
      <div className="bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 rounded-lg p-3.5 flex items-start gap-2.5 text-xs text-blue-900 dark:text-blue-200">
        <Info className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
        <p>
          <span className="font-bold">Scorecard Disclaimer: </span>
          The Business Health Index represents an algorithmic decision-support evaluation computed from historical sales, margins, and expenses. It is not an audited financial guarantee or certified credit rating.
        </p>
      </div>

      {/* Fallback Warning Banner */}
      {healthData?.is_fallback && (
        <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div className="text-xs text-amber-900 dark:text-amber-200">
            <span className="font-bold">Heuristic Baseline Scoring: </span>
            {healthData.warning_message || 'Computed using weighted financial ratio rules due to limited multi-period historical balance sheets.'}
          </div>
        </div>
      )}

      {isLoading ? (
        <Card className="p-12 text-center">
          <Spinner size="lg" className="mx-auto mb-3" />
          <p className="text-sm font-semibold text-surface-900 dark:text-surface-100">Evaluating Health Telemetry from Ledger...</p>
        </Card>
      ) : isError || !healthData ? (
        <Card className="p-8 text-center border-danger-200">
          <p className="text-sm font-semibold text-danger-600">Health Evaluation Unavailable</p>
          <p className="text-xs text-surface-500 mt-1 mb-4">Could not calculate health score. Ensure company records exist.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Health Card */}
          <Card className="lg:col-span-1 text-center p-6 flex flex-col justify-center items-center">
            <div className={`w-32 h-32 rounded-full border-8 ${
              healthData.health_score >= 80 ? 'border-emerald-500 bg-emerald-50/30' :
              healthData.health_score >= 60 ? 'border-indigo-500 bg-indigo-50/30' :
              healthData.health_score >= 40 ? 'border-amber-500 bg-amber-50/30' :
              'border-rose-500 bg-rose-50/30'
            } flex flex-col items-center justify-center mb-4`}>
              <span className="text-4xl font-black text-surface-900 dark:text-surface-100">
                {Math.round(healthData.health_score)}
              </span>
              <span className="text-[10px] text-surface-400 uppercase font-bold tracking-wider">Out of 100</span>
            </div>
            <h2 className="text-lg font-bold text-surface-900 dark:text-surface-100">
              Grade: {healthData.health_grade}
            </h2>
            <Badge
              variant={
                healthData.risk_rating === 'LOW_RISK' ? 'success' :
                healthData.risk_rating === 'MODERATE_RISK' ? 'warning' : 'danger'
              }
              className="mt-2 text-xs font-semibold"
            >
              Risk: {healthData.risk_rating}
            </Badge>
          </Card>

          {/* Sub-Scores & Recommendations */}
          <Card className="lg:col-span-2 space-y-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                <span>Financial Sub-Pillar Scores</span>
              </CardTitle>
              <CardDescription>Pillar performance calculated from live ledger transactions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {healthData.sub_scores && Object.keys(healthData.sub_scores).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(healthData.sub_scores).map(([key, score]) => (
                    <div key={key} className="space-y-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="capitalize text-surface-700 dark:text-surface-300">{key.replace(/_/g, ' ')}</span>
                        <span className="text-surface-900 dark:text-surface-100">{Math.round(score)} / 100</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-surface-200 dark:bg-surface-800 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            score >= 70 ? 'bg-emerald-600' : score >= 50 ? 'bg-amber-500' : 'bg-rose-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-surface-500">No sub-pillar metrics available.</p>
              )}

              <div className="pt-4 border-t border-surface-100 dark:border-surface-800 space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-surface-400">AI Strategic Recommendations</h4>
                {healthData.recommendations && healthData.recommendations.length > 0 ? (
                  healthData.recommendations.map((rec, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-surface-700 dark:text-surface-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-surface-500">Operational performance is within normal bounds. Continue monitoring monthly run-rates.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Audit History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5 text-surface-500" />
            <span>Business Health Audit History</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {historyItems.length === 0 ? (
            <p className="text-xs text-surface-500 text-center py-6">No previous business health evaluations recorded.</p>
          ) : (
            <Table columns={historyColumns} data={historyItems} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
