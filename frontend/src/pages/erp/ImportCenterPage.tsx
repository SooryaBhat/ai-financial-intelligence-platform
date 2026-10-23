import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  UploadCloud,
  FileSpreadsheet,
  FileText,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  Download,
  Package,
  ShoppingCart,
  PackageCheck,
  Layers,
  Receipt,
  FileCheck,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { importService } from '@/services/erp.service'
import { cn } from '@/lib/utils'

export type EntityType = 'products' | 'sales' | 'inventory' | 'expenses' | 'invoices'

interface EntityOption {
  id: EntityType
  title: string
  subtitle: string
  icon: React.ComponentType<{ className?: string }>
  badgeColor: string
}

const ENTITY_OPTIONS: EntityOption[] = [
  {
    id: 'products',
    title: 'Products & SKUs',
    subtitle: 'Import product catalog, pricing, SKUs & tax rates',
    icon: Package,
    badgeColor: 'text-teal-700 bg-teal-50 border-teal-200',
  },
  {
    id: 'sales',
    title: 'Sales & Sale Items',
    subtitle: 'Commercial orders with multi-item line products',
    icon: ShoppingCart,
    badgeColor: 'text-emerald-700 bg-emerald-50 border-emerald-200',
  },
  {
    id: 'inventory',
    title: 'Stock Balances & Adjustments',
    subtitle: 'Audit quantities, stock delta movements & reorder levels',
    icon: PackageCheck,
    badgeColor: 'text-blue-700 bg-blue-50 border-blue-200',
  },
  {
    id: 'expenses',
    title: 'Operating Expenses',
    subtitle: 'Expense vouchers, payment modes & receipts',
    icon: Layers,
    badgeColor: 'text-amber-700 bg-amber-50 border-amber-200',
  },
  {
    id: 'invoices',
    title: 'Invoices (Receivable & Payable)',
    subtitle: 'Official tax invoices, totals, dates & counterparties',
    icon: Receipt,
    badgeColor: 'text-violet-700 bg-violet-50 border-violet-200',
  },
]

type Step = 'select' | 'map' | 'validate' | 'confirm' | 'results' | 'pdf_review'

export const ImportCenterPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'import' | 'history'>('import')
  const [step, setStep] = useState<Step>('select')
  const [selectedEntity, setSelectedEntity] = useState<EntityType>('products')

  // File & Parsing state
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isParsing, setIsParsing] = useState(false)
  const [parsedData, setParsedData] = useState<{
    file_name: string
    source_format: string
    headers: string[]
    sheet_names?: string[]
    selected_sheet?: string
    total_rows: number
    preview_rows: any[]
    all_rows: any[]
    suggested_mapping: Record<string, string>
  } | null>(null)

  // Mapping state
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({})
  const [entitySchema, setEntitySchema] = useState<any>(null)

  // Validation state
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<{
    valid: boolean
    total_rows: number
    valid_rows: number
    warning_rows: number
    invalid_rows: number
    duplicate_rows: number
    row_results: any[]
  } | null>(null)
  const [previewFilter, setPreviewFilter] = useState<'all' | 'valid' | 'warning' | 'invalid'>('all')

  // Execution state
  const [conflictPolicy, setConflictPolicy] = useState<'skip' | 'update'>('skip')
  const [isImporting, setIsImporting] = useState(false)
  const [executionResult, setExecutionResult] = useState<any>(null)

  // PDF Extraction state
  const [pdfExtraction, setPdfExtraction] = useState<any>(null)
  const [isExtractingPdf, setIsExtractingPdf] = useState(false)
  const [pdfRecordType, setPdfRecordType] = useState<'invoice' | 'expense'>('invoice')
  const [pdfFormData, setPdfFormData] = useState<any>({})

  // History query
  const { data: historyData, refetch: refetchHistory, isLoading: isLoadingHistory } = useQuery({
    queryKey: ['importHistory'],
    queryFn: () => importService.getHistory(),
    enabled: activeTab === 'history',
  })

  // Load Schema when entity changes
  useEffect(() => {
    importService
      .getSchema(selectedEntity)
      .then((schema) => setEntitySchema(schema))
      .catch((err) => toast.error(`Failed to load schema: ${err.message}`))
  }, [selectedEntity])

  // ── Handler: File Select & Parse ─────────────────────────────
  const handleFileUpload = async (file: File) => {
    setSelectedFile(file)
    const ext = file.name.split('.').pop()?.toLowerCase()

    if (ext === 'pdf') {
      // PDF workflow
      setIsExtractingPdf(true)
      try {
        const extraction = await importService.extractPdf(file)
        setPdfExtraction(extraction)
        const candidates = extraction.candidate_fields || {}
        setPdfRecordType(extraction.document_type === 'receipt' ? 'expense' : 'invoice')
        setPdfFormData({
          document_number: candidates.document_number?.value || '',
          issue_date: candidates.issue_date?.value || new Date().toISOString().split('T')[0],
          due_date: candidates.due_date?.value || '',
          party_name: candidates.counterparty?.vendor || candidates.counterparty?.customer || '',
          subtotal: candidates.subtotal?.value || 0,
          tax_amount: candidates.tax_amount?.value || 0,
          total_amount: candidates.total_amount?.value || 0,
          currency: candidates.currency?.value || 'USD',
          description: `Extracted from ${file.name}`,
          notes: '',
        })
        setStep('pdf_review')
        toast.success('PDF text and financial data extracted for review!')
      } catch (err: any) {
        toast.error(err.response?.data?.detail || err.message || 'Failed to extract PDF')
      } finally {
        setIsExtractingPdf(false)
      }
      return
    }

    // CSV / XLSX workflow
    setIsParsing(true)
    try {
      const data = await importService.parseFile(file, selectedEntity)
      setParsedData(data)
      setColumnMapping(data.suggested_mapping || {})
      setStep('map')
      toast.success(`Parsed ${data.total_rows} rows from ${file.name}`)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.message || 'Failed to parse file')
    } finally {
      setIsParsing(false)
    }
  }

  // ── Handler: Run Validation ──────────────────────────────────
  const handleValidate = async () => {
    if (!parsedData) return
    setIsValidating(true)
    try {
      const result = await importService.validateBatch({
        entity_type: selectedEntity,
        column_mapping: columnMapping,
        rows: parsedData.all_rows,
      })
      setValidationResult(result)
      setStep('validate')
      if (result.invalid_rows > 0) {
        toast.error(`Validation found ${result.invalid_rows} rows with errors.`)
      } else {
        toast.success(`All ${result.valid_rows} rows validated successfully!`)
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.message || 'Validation failed')
    } finally {
      setIsValidating(false)
    }
  }

  // ── Handler: Confirm Execution ───────────────────────────────
  const handleConfirmImport = async () => {
    if (!validationResult) return
    setIsImporting(true)
    try {
      const idempotencyKey = crypto.randomUUID()
      const summary = await importService.confirmBatch({
        entity_type: selectedEntity,
        validated_rows: validationResult.row_results,
        conflict_policy: conflictPolicy,
        idempotency_key: idempotencyKey,
        file_name: parsedData?.file_name,
        source_format: parsedData?.source_format,
      })
      setExecutionResult(summary)
      setStep('results')
      toast.success(`Import complete! ${summary.created_count} created, ${summary.updated_count} updated.`)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.message || 'Import failed')
    } finally {
      setIsImporting(false)
    }
  }

  // ── Handler: Create PDF Record ───────────────────────────────
  const handleCreatePdfRecord = async () => {
    try {
      await importService.createPdfRecord({
        record_type: pdfRecordType,
        data: pdfFormData,
      })
      toast.success(`Successfully created ${pdfRecordType} record from PDF!`)
      setStep('select')
      setSelectedFile(null)
      setPdfExtraction(null)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.message || 'Failed to save record')
    }
  }

  // ── Reset Wizard ─────────────────────────────────────────────
  const handleReset = () => {
    setStep('select')
    setSelectedFile(null)
    setParsedData(null)
    setColumnMapping({})
    setValidationResult(null)
    setExecutionResult(null)
    setPdfExtraction(null)
  }

  // Filtered rows for preview
  const displayRows = validationResult?.row_results?.filter((r) => {
    if (previewFilter === 'all') return true
    if (previewFilter === 'valid') return r.status === 'valid'
    if (previewFilter === 'warning') return r.status === 'warning'
    if (previewFilter === 'invalid') return r.status === 'invalid'
    return true
  }) || []

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">ERP Data Import Center</h1>
            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-teal-50 text-teal-700 border border-teal-200">
              Safe Multi-Tenant
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Upload CSV, Excel, or PDF documents, map fields to ERP models, review validation diagnostics, and confirm imports.
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('import')}
            className={cn(
              'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
              activeTab === 'import' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            )}
          >
            Import Wizard
          </button>
          <button
            onClick={() => {
              setActiveTab('history')
              refetchHistory()
            }}
            className={cn(
              'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
              activeTab === 'history' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            )}
          >
            Import History
          </button>
        </div>
      </div>

      {activeTab === 'history' ? (
        /* History View */
        <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Recent Import Batches</h3>
            <button
              onClick={() => refetchHistory()}
              className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-teal-700 font-medium"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', isLoadingHistory && 'animate-spin')} />
              Refresh
            </button>
          </div>

          {isLoadingHistory ? (
            <div className="py-12 text-center text-xs text-slate-400">Loading import batches...</div>
          ) : !historyData || historyData.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500 bg-slate-50 rounded-lg border border-dashed border-slate-200">
              No import batches recorded yet. Run your first import using the wizard!
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                  <tr>
                    <th className="py-2.5 px-3">Batch ID</th>
                    <th className="py-2.5 px-3">Entity</th>
                    <th className="py-2.5 px-3">File Name</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Imported Rows</th>
                    <th className="py-2.5 px-3">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {historyData.map((b: any) => (
                    <tr key={b.id || b.batch_id} className="hover:bg-slate-50/50">
                      <td className="py-2.5 px-3 font-mono text-slate-500">{(b.id || b.batch_id).slice(0, 8)}...</td>
                      <td className="py-2.5 px-3 font-medium capitalize text-slate-800">{b.entity_type}</td>
                      <td className="py-2.5 px-3 text-slate-600">{b.file_name || 'N/A'}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={cn(
                            'px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wider',
                            b.status === 'completed'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : b.status === 'failed'
                              ? 'bg-rose-50 text-rose-700 border border-rose-200'
                              : 'bg-amber-50 text-amber-700 border border-amber-200'
                          )}
                        >
                          {b.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-700">
                        {b.imported_rows ?? (b.created_count ?? 0) + (b.updated_count ?? 0)} / {b.total_rows ?? b.total_submitted ?? 0}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {new Date(b.created_at || b.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        /* Wizard Steps */
        <div className="space-y-6">
          {/* Step Progress Bar */}
          <div className="flex items-center justify-between max-w-3xl mx-auto px-4">
            {[
              { id: 'select', label: '1. Select & Upload' },
              { id: 'map', label: '2. Map Columns' },
              { id: 'validate', label: '3. Validate & Preview' },
              { id: 'confirm', label: '4. Confirm Import' },
              { id: 'results', label: '5. Results' },
            ].map((s, idx) => {
              const isCurrent = step === s.id
              const isPassed =
                ['select', 'map', 'validate', 'confirm', 'results'].indexOf(step) >
                ['select', 'map', 'validate', 'confirm', 'results'].indexOf(s.id)

              return (
                <div key={s.id} className="flex items-center gap-2">
                  <div
                    className={cn(
                      'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors',
                      isCurrent
                        ? 'bg-teal-700 text-white shadow-sm'
                        : isPassed
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-100 text-slate-400'
                    )}
                  >
                    {isPassed ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : idx + 1}
                  </div>
                  <span
                    className={cn(
                      'text-xs font-medium hidden sm:inline',
                      isCurrent ? 'text-slate-900 font-semibold' : 'text-slate-500'
                    )}
                  >
                    {s.label.split('. ')[1]}
                  </span>
                </div>
              )
            })}
          </div>

          {/* STEP A: Select Entity & Upload File */}
          {step === 'select' && (
            <div className="space-y-6">
              {/* Entity Selector Cards */}
              <div>
                <h3 className="text-sm font-semibold text-slate-800 mb-3">1. Select Target ERP Entity</h3>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                  {ENTITY_OPTIONS.map((opt) => {
                    const Icon = opt.icon
                    const isSelected = selectedEntity === opt.id
                    return (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => setSelectedEntity(opt.id)}
                        className={cn(
                          'p-4 rounded-xl border text-left transition-all relative flex flex-col justify-between h-32',
                          isSelected
                            ? 'bg-teal-50/50 border-teal-600 shadow-sm ring-1 ring-teal-600'
                            : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                        )}
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className={cn('p-2 rounded-lg border', opt.badgeColor)}>
                              <Icon className="w-4 h-4" />
                            </span>
                            {isSelected && <CheckCircle2 className="w-4 h-4 text-teal-600" />}
                          </div>
                          <h4 className="text-xs font-bold text-slate-900">{opt.title}</h4>
                        </div>
                        <p className="text-[11px] text-slate-500 line-clamp-2 mt-1">{opt.subtitle}</p>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Upload Dropzone */}
              <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
                <div className="max-w-xl mx-auto text-center space-y-4">
                  <div className="w-12 h-12 mx-auto rounded-full bg-teal-50 flex items-center justify-center text-teal-700 border border-teal-200">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Upload Data File</h3>
                    <p className="text-xs text-slate-500 mt-1">
                      Drag & drop your file here, or click to browse. Max size 10MB.
                    </p>
                  </div>

                  {/* Format Pills */}
                  <div className="flex items-center justify-center gap-2">
                    <span className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 text-slate-700 text-xs font-medium">
                      <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
                      .CSV
                    </span>
                    <span className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 text-slate-700 text-xs font-medium">
                      <FileSpreadsheet className="w-3.5 h-3.5 text-blue-600" />
                      .XLSX
                    </span>
                    <span className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 text-slate-700 text-xs font-medium">
                      <FileText className="w-3.5 h-3.5 text-rose-600" />
                      .PDF (Doc Extract)
                    </span>
                  </div>

                  <input
                    type="file"
                    id="fileUpload"
                    accept=".csv,.xlsx,.pdf"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        handleFileUpload(e.target.files[0])
                      }
                    }}
                  />
                  <label
                    htmlFor="fileUpload"
                    className={cn(
                      'inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-semibold text-white bg-teal-700 hover:bg-teal-800 transition-colors cursor-pointer shadow-sm',
                      (isParsing || isExtractingPdf) && 'opacity-60 pointer-events-none'
                    )}
                  >
                    {isParsing || isExtractingPdf ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Processing Document...
                      </>
                    ) : (
                      <>Choose Business File</>
                    )}
                  </label>
                  {selectedFile && (
                    <div className="text-xs text-slate-500 font-mono">
                      Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                    </div>
                  )}
                </div>
              </div>

              {/* Safety Guidance Notice */}
              <div className="rounded-lg bg-slate-50 border border-slate-200 p-4 text-xs text-slate-600 flex items-start gap-3">
                <ShieldCheck className="w-5 h-5 text-teal-700 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-bold text-slate-900">Safe Import Guarantee</span>
                  <p>
                    Files are safely parsed without spreadsheet macro or formula execution. No records are written to the database until you review the full validation preview and explicitly confirm the import.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* STEP B: Map Columns */}
          {step === 'map' && parsedData && (
            <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-6 shadow-sm">
              <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Map Columns to ERP Fields</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Match headers from <span className="font-semibold text-slate-700">{parsedData.file_name}</span> to the {selectedEntity} schema.
                  </p>
                </div>
                <button
                  onClick={handleReset}
                  className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 font-medium"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Cancel & Restart
                </button>
              </div>

              {/* Mapping Table */}
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                    <tr>
                      <th className="py-2.5 px-4 w-1/3">Source File Header</th>
                      <th className="py-2.5 px-4 w-1/3">Sample Value</th>
                      <th className="py-2.5 px-4 w-1/3">Target ERP Field</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {parsedData.headers.map((header) => {
                      const sampleVal = parsedData.preview_rows[0]?.[header] ?? '—'
                      const currentMappedField = columnMapping[header] || ''

                      return (
                        <tr key={header} className="hover:bg-slate-50/60">
                          <td className="py-3 px-4 font-mono font-medium text-slate-800">{header}</td>
                          <td className="py-3 px-4 text-slate-500 truncate max-w-xs">{String(sampleVal)}</td>
                          <td className="py-3 px-4">
                            <select
                              value={currentMappedField}
                              onChange={(e) => {
                                setColumnMapping((prev) => ({
                                  ...prev,
                                  [header]: e.target.value,
                                }))
                              }}
                              className="w-full text-xs rounded-md border border-slate-300 py-1.5 px-2 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-600"
                            >
                              <option value="">— Do Not Import (Skip) —</option>
                              {entitySchema?.fields?.map((f: any) => (
                                <option key={f.name} value={f.name}>
                                  {f.label} {f.required ? '(* Required)' : '(Optional)'}
                                </option>
                              ))}
                            </select>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setStep('select')}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Back
                </button>
                <button
                  type="button"
                  onClick={handleValidate}
                  disabled={isValidating}
                  className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold shadow-sm transition-colors disabled:opacity-60"
                >
                  {isValidating ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Validating Rows...
                    </>
                  ) : (
                    <>
                      Validate Records
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* STEP C: Validate & Preview */}
          {step === 'validate' && validationResult && (
            <div className="space-y-6">
              {/* Validation Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Rows</span>
                  <div className="text-xl font-bold text-slate-900 mt-1">{validationResult.total_rows}</div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/20 shadow-sm">
                  <span className="text-[11px] font-semibold text-emerald-700 uppercase">Valid Rows</span>
                  <div className="text-xl font-bold text-emerald-700 mt-1">{validationResult.valid_rows}</div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20 shadow-sm">
                  <span className="text-[11px] font-semibold text-amber-700 uppercase">Warnings / Conflicts</span>
                  <div className="text-xl font-bold text-amber-700 mt-1">{validationResult.warning_rows}</div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/20 shadow-sm">
                  <span className="text-[11px] font-semibold text-rose-700 uppercase">Invalid Rows</span>
                  <div className="text-xl font-bold text-rose-700 mt-1">{validationResult.invalid_rows}</div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase">File Duplicates</span>
                  <div className="text-xl font-bold text-slate-700 mt-1">{validationResult.duplicate_rows}</div>
                </div>
              </div>

              {/* Preview Table Header & Filter Tabs */}
              <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-200">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPreviewFilter('all')}
                      className={cn(
                        'px-2.5 py-1 text-xs font-semibold rounded-md transition-colors',
                        previewFilter === 'all' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      )}
                    >
                      All Rows ({validationResult.total_rows})
                    </button>
                    <button
                      onClick={() => setPreviewFilter('valid')}
                      className={cn(
                        'px-2.5 py-1 text-xs font-semibold rounded-md transition-colors',
                        previewFilter === 'valid' ? 'bg-emerald-700 text-white' : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                      )}
                    >
                      Valid ({validationResult.valid_rows})
                    </button>
                    <button
                      onClick={() => setPreviewFilter('warning')}
                      className={cn(
                        'px-2.5 py-1 text-xs font-semibold rounded-md transition-colors',
                        previewFilter === 'warning' ? 'bg-amber-600 text-white' : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                      )}
                    >
                      Warnings / Conflicts ({validationResult.warning_rows})
                    </button>
                    {validationResult.invalid_rows > 0 && (
                      <button
                        onClick={() => setPreviewFilter('invalid')}
                        className={cn(
                          'px-2.5 py-1 text-xs font-semibold rounded-md transition-colors',
                          previewFilter === 'invalid' ? 'bg-rose-700 text-white' : 'bg-rose-50 text-rose-700 hover:bg-rose-100'
                        )}
                      >
                        Errors ({validationResult.invalid_rows})
                      </button>
                    )}
                  </div>

                  {/* Export error report button */}
                  {validationResult.invalid_rows > 0 && (
                    <button
                      onClick={() => importService.exportErrors(validationResult.row_results)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                    >
                      <Download className="w-3.5 h-3.5 text-slate-500" />
                      Download Error CSV
                    </button>
                  )}
                </div>

                {/* Rows Table */}
                <div className="border border-slate-200 rounded-lg overflow-x-auto max-h-96">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold sticky top-0 z-10">
                      <tr>
                        <th className="py-2.5 px-3 w-16">Row #</th>
                        <th className="py-2.5 px-3 w-28">Status</th>
                        <th className="py-2.5 px-3">Normalized ERP Data</th>
                        <th className="py-2.5 px-3 w-1/3">Validation Diagnostics</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {displayRows.map((r) => (
                        <tr key={r.row_number} className="hover:bg-slate-50/50">
                          <td className="py-2.5 px-3 font-mono text-slate-500">{r.row_number}</td>
                          <td className="py-2.5 px-3">
                            <span
                              className={cn(
                                'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wider',
                                r.status === 'valid'
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : r.status === 'warning'
                                  ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                  : 'bg-rose-50 text-rose-700 border border-rose-200'
                              )}
                            >
                              {r.status}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 font-mono text-[11px] text-slate-700">
                            {JSON.stringify(r.normalized_data)}
                          </td>
                          <td className="py-2.5 px-3 text-xs">
                            {r.errors?.length > 0 && (
                              <div className="text-rose-700 font-medium space-y-0.5">
                                {r.errors.map((err: string, i: number) => (
                                  <div key={i} className="flex items-center gap-1">
                                    <XCircle className="w-3.5 h-3.5 shrink-0" />
                                    <span>{err}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                            {r.warnings?.length > 0 && (
                              <div className="text-amber-700 font-medium space-y-0.5 mt-1">
                                {r.warnings.map((warn: string, i: number) => (
                                  <div key={i} className="flex items-center gap-1">
                                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                                    <span>{warn}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                            {!r.errors?.length && !r.warnings?.length && (
                              <span className="text-slate-400">Ready for insertion</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Bottom Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                  <button
                    type="button"
                    onClick={() => setStep('map')}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    Back to Mapping
                  </button>
                  <button
                    type="button"
                    onClick={() => setStep('confirm')}
                    disabled={validationResult.valid_rows === 0}
                    className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold shadow-sm transition-colors disabled:opacity-60"
                  >
                    Proceed to Confirmation
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP D: Confirm Import */}
          {step === 'confirm' && validationResult && (
            <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-6 max-w-2xl mx-auto shadow-sm">
              <div className="text-center space-y-1">
                <div className="w-12 h-12 mx-auto rounded-full bg-teal-50 flex items-center justify-center text-teal-700 border border-teal-200 mb-2">
                  <FileCheck className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-slate-900">Review & Confirm ERP Import</h3>
                <p className="text-xs text-slate-500">
                  Please review the proposed operations before records are written to the database.
                </p>
              </div>

              {/* Import Impact Summary */}
              <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 space-y-3">
                <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-200">
                  <span className="text-slate-500">Target Entity:</span>
                  <span className="font-bold text-slate-900 capitalize">{selectedEntity}</span>
                </div>
                <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-200">
                  <span className="text-slate-500">Records to Import:</span>
                  <span className="font-bold text-emerald-700">{validationResult.valid_rows} rows</span>
                </div>
                {validationResult.invalid_rows > 0 && (
                  <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-200">
                    <span className="text-slate-500">Rejected Invalid Records:</span>
                    <span className="font-bold text-rose-700">{validationResult.invalid_rows} rows (will be skipped)</span>
                  </div>
                )}
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">File Name:</span>
                  <span className="font-mono text-slate-800">{parsedData?.file_name}</span>
                </div>
              </div>

              {/* Conflict Policy Selector */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-800">Existing Records Conflict Policy:</label>
                <div className="grid grid-cols-2 gap-3">
                  <label
                    className={cn(
                      'p-3 rounded-lg border text-xs cursor-pointer flex flex-col justify-between transition-all',
                      conflictPolicy === 'skip'
                        ? 'border-teal-600 bg-teal-50/40 ring-1 ring-teal-600'
                        : 'border-slate-200 hover:border-slate-300'
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="conflict"
                        value="skip"
                        checked={conflictPolicy === 'skip'}
                        onChange={() => setConflictPolicy('skip')}
                        className="text-teal-700 focus:ring-teal-700"
                      />
                      <span className="font-bold text-slate-900">Skip Existing (Safe)</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1 pl-6">
                      Leave existing records untouched; only insert new records.
                    </p>
                  </label>

                  <label
                    className={cn(
                      'p-3 rounded-lg border text-xs cursor-pointer flex flex-col justify-between transition-all',
                      conflictPolicy === 'update'
                        ? 'border-teal-600 bg-teal-50/40 ring-1 ring-teal-600'
                        : 'border-slate-200 hover:border-slate-300'
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="conflict"
                        value="update"
                        checked={conflictPolicy === 'update'}
                        onChange={() => setConflictPolicy('update')}
                        className="text-teal-700 focus:ring-teal-700"
                      />
                      <span className="font-bold text-slate-900">Update Existing</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1 pl-6">
                      Overwrite matched fields with the newly uploaded values.
                    </p>
                  </label>
                </div>
              </div>

              {/* Confirmation Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setStep('validate')}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Back
                </button>
                <button
                  type="button"
                  onClick={handleConfirmImport}
                  disabled={isImporting}
                  className="flex items-center gap-1.5 px-6 py-2.5 rounded-lg bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold shadow-sm transition-colors disabled:opacity-60"
                >
                  {isImporting ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Importing Records...
                    </>
                  ) : (
                    <>Confirm & Import {validationResult.valid_rows} Records</>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* STEP E: Execution Results */}
          {step === 'results' && executionResult && (
            <div className="bg-white rounded-xl border border-slate-200 p-8 space-y-6 max-w-xl mx-auto text-center shadow-sm">
              <div className="w-14 h-14 mx-auto rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-200">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Import Batch Completed</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Batch ID: <span className="font-mono text-slate-700">{executionResult.batch_id}</span>
                </p>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-4 gap-2 bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500">Created</span>
                  <div className="text-lg font-bold text-emerald-700 mt-1">{executionResult.created_count}</div>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500">Updated</span>
                  <div className="text-lg font-bold text-blue-700 mt-1">{executionResult.updated_count}</div>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500">Skipped</span>
                  <div className="text-lg font-bold text-slate-600 mt-1">{executionResult.skipped_count}</div>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500">Failed</span>
                  <div className="text-lg font-bold text-rose-700 mt-1">{executionResult.failed_count}</div>
                </div>
              </div>

              {executionResult.errors?.length > 0 && (
                <div className="text-left bg-rose-50 border border-rose-200 rounded-lg p-3 text-xs text-rose-700 space-y-1">
                  <span className="font-bold">Errors encountered during execution:</span>
                  {executionResult.errors.map((err: string, i: number) => (
                    <div key={i}>• {err}</div>
                  ))}
                </div>
              )}

              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-5 py-2.5 rounded-lg bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold shadow-sm transition-colors"
                >
                  Import Another File
                </button>
              </div>
            </div>
          )}

          {/* STEP F: PDF Interactive Review Screen */}
          {step === 'pdf_review' && pdfExtraction && (
            <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-6 shadow-sm">
              <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-slate-900">PDF Document Review & Field Editor</h3>
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded text-[11px] font-semibold',
                        pdfExtraction.arithmetic_check?.is_consistent
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      )}
                    >
                      {pdfExtraction.arithmetic_check?.is_consistent
                        ? '✓ Arithmetic Verified'
                        : '⚠ Arithmetic Discrepancy'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Extracted from <span className="font-semibold">{pdfExtraction.file_name}</span>. Review all candidate values before creating an official ERP entry.
                  </p>
                </div>
                <button
                  onClick={handleReset}
                  className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 font-medium"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Cancel
                </button>
              </div>

              {/* Form & Editable Fields */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2 space-y-4">
                  {/* Record Type Switch */}
                  <div className="flex items-center gap-4 bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <span className="text-xs font-bold text-slate-800">Target Record Type:</span>
                    <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 cursor-pointer">
                      <input
                        type="radio"
                        value="invoice"
                        checked={pdfRecordType === 'invoice'}
                        onChange={() => setPdfRecordType('invoice')}
                        className="text-teal-700"
                      />
                      Customer Invoice / Bill
                    </label>
                    <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 cursor-pointer">
                      <input
                        type="radio"
                        value="expense"
                        checked={pdfRecordType === 'expense'}
                        onChange={() => setPdfRecordType('expense')}
                        className="text-teal-700"
                      />
                      Expense Voucher / Receipt
                    </label>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Document / Invoice #
                      </label>
                      <input
                        type="text"
                        value={pdfFormData.document_number}
                        onChange={(e) => setPdfFormData({ ...pdfFormData, document_number: e.target.value })}
                        className="w-full text-xs rounded-md border border-slate-300 py-1.5 px-3 focus:outline-none focus:ring-1 focus:ring-teal-600"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Issue Date</label>
                      <input
                        type="date"
                        value={pdfFormData.issue_date}
                        onChange={(e) => setPdfFormData({ ...pdfFormData, issue_date: e.target.value })}
                        className="w-full text-xs rounded-md border border-slate-300 py-1.5 px-3 focus:outline-none focus:ring-1 focus:ring-teal-600"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Counterparty / Vendor / Customer
                      </label>
                      <input
                        type="text"
                        value={pdfFormData.party_name}
                        onChange={(e) => setPdfFormData({ ...pdfFormData, party_name: e.target.value })}
                        className="w-full text-xs rounded-md border border-slate-300 py-1.5 px-3 focus:outline-none focus:ring-1 focus:ring-teal-600"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Currency</label>
                      <input
                        type="text"
                        value={pdfFormData.currency}
                        onChange={(e) => setPdfFormData({ ...pdfFormData, currency: e.target.value })}
                        className="w-full text-xs rounded-md border border-slate-300 py-1.5 px-3 focus:outline-none focus:ring-1 focus:ring-teal-600 uppercase"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Subtotal</label>
                      <input
                        type="number"
                        step="0.01"
                        value={pdfFormData.subtotal}
                        onChange={(e) => setPdfFormData({ ...pdfFormData, subtotal: parseFloat(e.target.value) || 0 })}
                        className="w-full text-xs rounded-md border border-slate-300 py-1.5 px-3 focus:outline-none focus:ring-1 focus:ring-teal-600"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Tax Amount</label>
                      <input
                        type="number"
                        step="0.01"
                        value={pdfFormData.tax_amount}
                        onChange={(e) => setPdfFormData({ ...pdfFormData, tax_amount: parseFloat(e.target.value) || 0 })}
                        className="w-full text-xs rounded-md border border-slate-300 py-1.5 px-3 focus:outline-none focus:ring-1 focus:ring-teal-600"
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Total Amount (* Required)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={pdfFormData.total_amount}
                        onChange={(e) => setPdfFormData({ ...pdfFormData, total_amount: parseFloat(e.target.value) || 0 })}
                        className="w-full text-xs font-bold text-slate-900 rounded-md border border-teal-600 py-2 px-3 focus:outline-none focus:ring-1 focus:ring-teal-600"
                      />
                    </div>
                  </div>
                </div>

                {/* Raw Text Preview */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800">Extracted PDF Text Preview</span>
                    <span className="text-[10px] text-slate-400">Untrusted source text</span>
                  </div>
                  <div className="h-72 overflow-y-auto bg-slate-900 text-slate-200 font-mono text-[11px] p-3 rounded-lg">
                    {pdfExtraction.raw_text_preview || 'No readable text extracted.'}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Discard
                </button>
                <button
                  type="button"
                  onClick={handleCreatePdfRecord}
                  disabled={!pdfFormData.total_amount}
                  className="px-6 py-2.5 rounded-lg bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold shadow-sm transition-colors disabled:opacity-50"
                >
                  Confirm & Create {pdfRecordType === 'invoice' ? 'Invoice' : 'Expense'} Record
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ImportCenterPage
