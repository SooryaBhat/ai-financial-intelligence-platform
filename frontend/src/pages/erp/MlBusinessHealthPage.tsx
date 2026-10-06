import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { BrainCircuit, ShieldCheck, CheckCircle2 } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'

export const MlBusinessHealthPage: React.FC = () => {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['ml-business-health'],
    queryFn: () => mlService.predictBusinessHealth({ revenue_growth: 0.18, profit_margin: 0.22, expense_control: 0.85, inventory_turnover: 4.5, payment_collection: 0.92 }),
  })

  const healthData = (data as {
    health_score?: number
    health_grade?: string
    risk_rating?: string
    sub_scores?: Record<string, number>
    recommendations?: string[]
  }) || {}

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100 flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-indigo-600" />
          <span>Business Health Score & Risk Evaluator</span>
        </h1>
        <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
          Composite financial health index (0–100), letter grade, and AI advisory recommendations
        </p>
      </div>

      {isLoading ? (
        <Card className="p-12 text-center">
          <Spinner size="lg" className="mx-auto mb-3" />
          <p className="text-sm font-semibold text-surface-900 dark:text-surface-100">Evaluating Health Telemetry...</p>
        </Card>
      ) : isError ? (
        <Card className="p-8 text-center border-danger-200">
          <p className="text-sm font-semibold text-danger-600">Evaluation Warning</p>
          <p className="text-xs text-surface-500 mt-1 mb-4">Could not calculate health score.</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Health Card */}
          <Card className="lg:col-span-1 text-center p-6 flex flex-col justify-center items-center">
            <div className="w-32 h-32 rounded-full border-8 border-emerald-500 flex flex-col items-center justify-center bg-emerald-50/30 dark:bg-emerald-950/20 mb-4">
              <span className="text-4xl font-black text-surface-900 dark:text-surface-100">
                {healthData.health_score || 84.2}
              </span>
              <span className="text-[10px] text-surface-400 uppercase font-bold tracking-wider">Out of 100</span>
            </div>
            <h2 className="text-lg font-bold text-surface-900 dark:text-surface-100">
              Grade: {healthData.health_grade || 'A'}
            </h2>
            <Badge variant="success" className="mt-2 text-xs font-semibold">
              Risk: {healthData.risk_rating || 'LOW_RISK'}
            </Badge>
          </Card>

          {/* Sub-Scores & Recommendations */}
          <Card className="lg:col-span-2 space-y-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                <span>Financial Sub-Pillar Scores</span>
              </CardTitle>
              <CardDescription>Weighted component scores evaluated across company metrics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                {Object.entries(healthData.sub_scores || { revenue_growth: 85, profit_margin: 78, expense_control: 92, collection: 90 }).map(([key, score]) => (
                  <div key={key} className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="capitalize text-surface-700 dark:text-surface-300">{key.replace(/_/g, ' ')}</span>
                      <span className="text-surface-900 dark:text-surface-100">{score} / 100</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-surface-200 dark:bg-surface-800 overflow-hidden">
                      <div className="h-full bg-primary-600 rounded-full" style={{ width: `${Math.min(100, Math.max(0, score))}%` }} />
                    </div>
                  </div>
                ))}
              </div>

              <div className="pt-4 border-t border-surface-100 dark:border-surface-800 space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-surface-400">AI Strategic Recommendations</h4>
                {(healthData.recommendations || [
                  'Maintain optimal payment collection pace to preserve strong cash liquidity.',
                  'Expand high-margin product categories to accelerate revenue trajectory.',
                ]).map((rec, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-surface-700 dark:text-surface-300">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <span>{rec}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
