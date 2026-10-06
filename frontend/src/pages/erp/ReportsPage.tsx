import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, FileText, Download } from 'lucide-react'
import { reportService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Badge } from '@/components/ui/Badge'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'
import { formatDate } from '@/lib/utils'

interface ReportRecord {
  id: string
  title: string
  report_type: string
  status: string
  created_at?: string
  [key: string]: unknown
}

export const ReportsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [formData, setFormData] = useState({
    title: 'Q3 Financial Audit Report',
    report_type: 'financial_summary',
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportService.list(),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => reportService.create(payload),
    onSuccess: () => {
      toast.success('Report generation triggered')
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to generate report'),
  })

  const columns: Column<ReportRecord>[] = [
    {
      key: 'title',
      header: 'Report Title',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 font-bold text-xs">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">{row.title}</span>
            <p className="text-[10px] text-surface-400 uppercase tracking-wider">{row.report_type}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => {
        const isReady = row.status === 'completed' || row.status === 'ready'
        return <Badge variant={isReady ? 'success' : 'info'}>{row.status || 'Generating'}</Badge>
      },
    },
    { key: 'created_at', header: 'Generated On', render: (row) => (row.created_at ? formatDate(row.created_at) : '-') },
    {
      key: 'actions',
      header: 'Actions',
      className: 'text-right',
      render: () => (
        <Button variant="outline" size="sm" leftIcon={<Download className="w-3.5 h-3.5" />}>
          Export PDF
        </Button>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load reports" onRetry={() => refetch()} />

  const items = (Array.isArray(data) ? data : data?.items || []) as ReportRecord[]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Financial Reports & Audits</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Automated PDF balance sheets, income statements, and tax compliance exports
          </p>
        </div>
        <Button variant="primary" onClick={() => setIsModalOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Generate Report
        </Button>
      </div>

      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No reports generated yet." />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Generate New Financial Report">
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input label="Report Title" value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} required />
          <Select
            label="Report Type"
            value={formData.report_type}
            onChange={(e) => setFormData({ ...formData, report_type: e.target.value })}
            options={[
              { label: 'Executive Financial Summary', value: 'financial_summary' },
              { label: 'Profit & Loss Statement', value: 'profit_loss' },
              { label: 'Sales & Inventory Velocity', value: 'sales_inventory' },
              { label: 'Tax & Ledger Audit Trail', value: 'tax_audit' },
            ]}
          />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Compile Report</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
