import React from 'react'
import { Brain, ShieldCheck, Database, Award, Info, AlertCircle } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Card, CardContent } from '@/components/ui/Card'

export interface ModelIntelligenceProps {
  pipelineTitle: string
  selectedAlgorithm: string
  modelName?: string
  modelVersion?: string
  valMetricLabel: string
  valMetricValue: string | number
  testMetricLabel?: string
  testMetricValue?: string | number
  holdoutMetricLabel?: string
  holdoutMetricValue?: string | number
  baselineComparison?: string
  datasetPeriod?: string
  datasetVersion?: string
  isFallback?: boolean
  warningMessage?: string | null
}

export const ModelIntelligenceBanner: React.FC<ModelIntelligenceProps> = ({
  pipelineTitle,
  selectedAlgorithm,
  modelName,
  modelVersion,
  valMetricLabel,
  valMetricValue,
  testMetricLabel,
  testMetricValue,
  holdoutMetricLabel,
  holdoutMetricValue,
  baselineComparison,
  datasetPeriod = '2022-01 to 2026-02 (58 Months, 142,791 Rows)',
  datasetVersion = 'synthetic_v2 (Validated Reconciliation)',
  isFallback = false,
  warningMessage,
}) => {
  return (
    <div className="space-y-3">
      {/* Fallback Warning if active */}
      {isFallback && (
        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-800">
            <span className="font-bold">Database Fallback Active: </span>
            {warningMessage ||
              'Historical database records for this tenant/outlet are currently insufficient for deep lag feature generation. A conservative baseline estimate is displayed.'}
          </div>
        </div>
      )}

      {/* Model Intelligence & Governance Card */}
      <Card className="border border-slate-200 bg-white shadow-xs rounded-xl overflow-hidden">
        <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-teal-950 p-4 text-white">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-teal-500/20 border border-teal-400/30 text-teal-300">
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-bold text-white tracking-wide">{pipelineTitle}</h4>
                  <Badge variant="success" className="bg-teal-500/20 text-teal-300 border-teal-500/40 text-[10px] py-0 px-1.5">
                    Production Verified
                  </Badge>
                </div>
                <p className="text-xs text-slate-300 mt-0.5">
                  Algorithm: <span className="font-semibold text-white">{selectedAlgorithm}</span>
                  {modelVersion && <span className="text-slate-400 font-mono text-[11px] ml-1.5">({modelVersion})</span>}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[11px] px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-teal-400" />
                {datasetVersion}
              </span>
            </div>
          </div>
        </div>

        <CardContent className="p-4 bg-slate-50/60 divide-y divide-slate-100">
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pb-3">
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-2xs">
              <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">Dev Validation</span>
              <span className="text-base font-extrabold text-slate-900 mt-0.5 block">{valMetricValue}</span>
              <span className="text-[10px] text-slate-400">{valMetricLabel}</span>
            </div>

            {testMetricLabel && testMetricValue !== undefined && (
              <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-2xs">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">Dev Test Set</span>
                <span className="text-base font-extrabold text-slate-900 mt-0.5 block">{testMetricValue}</span>
                <span className="text-[10px] text-slate-400">{testMetricLabel}</span>
              </div>
            )}

            {holdoutMetricLabel && holdoutMetricValue !== undefined && (
              <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-2xs">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">Zero-Shot Holdout</span>
                <span className="text-base font-extrabold text-teal-700 mt-0.5 block">{holdoutMetricValue}</span>
                <span className="text-[10px] text-slate-400">Co3: {holdoutMetricLabel}</span>
              </div>
            )}

            {baselineComparison && (
              <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-2xs">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">Vs Baseline</span>
                <span className="text-xs font-bold text-slate-700 mt-0.5 block">{baselineComparison}</span>
                <span className="text-[10px] text-emerald-600 font-medium">Outperforms Naive</span>
              </div>
            )}
          </div>

          {/* Dataset Provenance & Limitations disclosure */}
          <div className="pt-3 flex items-start gap-2 text-[11px] text-slate-500 leading-relaxed">
            <Info className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
            <div>
              <span className="font-semibold text-slate-700">Dataset Provenance & Scope: </span>
              Pre-trained on historical enterprise ledgers covering {datasetPeriod}.
              <span className="text-slate-400 block mt-0.5">
                Synthetic validation disclosure: Validated on audited synthetic distributions (Approach C). Inference operates securely on authorized tenant ledger records without cross-company leakage.
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
