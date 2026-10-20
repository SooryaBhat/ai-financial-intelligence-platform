import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { AlertTriangle, ShieldAlert, CheckCircle } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { useToast } from '@/hooks/useToast'

export const MlAnomaliesPage: React.FC = () => {
  const toast = useToast()
  const [netAmount, setNetAmount] = useState(125000)
  const [discountPct, setDiscountPct] = useState(15)

  const scanMutation = useMutation({
    mutationFn: (payload: { netAmount: number; discountPct: number }) =>
      mlService.predictAnomaly(payload.netAmount, payload.discountPct),
    onError: () => toast.error('Anomaly scan failed'),
  })

  const result = (scanMutation.data as {
    is_anomaly?: boolean
    anomaly_score?: number
    severity?: string
    confidence?: number
    reason?: string
  }) || null

  const handleScan = (e: React.FormEvent) => {
    e.preventDefault()
    scanMutation.mutate({ netAmount, discountPct })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Transaction Anomaly Inspector"
        description="Scan invoices and commercial transactions for statistical outliers and fraud signals using Isolation Forest ML"
        icon={<AlertTriangle className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">ML Engine</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'Anomaly Detection' },
        ]}
      />

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
                label="Invoice Net Amount ($)"
                type="number"
                value={netAmount}
                onChange={(e) => setNetAmount(Number(e.target.value))}
                required
              />
              <Input
                label="Applied Discount (%)"
                type="number"
                step="0.1"
                value={discountPct}
                onChange={(e) => setDiscountPct(Number(e.target.value))}
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
                Submit transaction parameters to run Isolation Forest inference.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-surface-500">Anomaly Classification</span>
                  <Badge variant={result.is_anomaly ? 'danger' : 'success'} className="text-xs font-bold gap-1">
                    {result.is_anomaly ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
                    {result.is_anomaly ? 'ANOMALY DETECTED' : 'NORMAL TRANSACTION'}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-surface-100 dark:bg-surface-800">
                    <span className="text-[10px] text-surface-400 uppercase font-bold">Severity Rating</span>
                    <p className="text-sm font-bold text-surface-900 dark:text-surface-100">{result.severity || 'LOW'}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-surface-100 dark:bg-surface-800">
                    <span className="text-[10px] text-surface-400 uppercase font-bold">Confidence</span>
                    <p className="text-sm font-bold text-surface-900 dark:text-surface-100">{result.confidence || 99}%</p>
                  </div>
                </div>

                {result.reason && (
                  <div className="p-3.5 rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50/50 dark:bg-rose-950/20 text-xs text-rose-800 dark:text-rose-300">
                    <p className="font-bold mb-1">Diagnostic Root Cause:</p>
                    <p>{result.reason}</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
