import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Receipt } from 'lucide-react'
import { invoiceService, customerService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Badge } from '@/components/ui/Badge'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Search } from '@/components/ui/Search'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { PageHeader } from '@/components/ui/PageHeader'
import { useToast } from '@/hooks/useToast'
import { formatCurrency, formatDate } from '@/lib/utils'

interface InvoiceRecord {
  id: string
  invoice_number?: string
  invoice_type?: string
  subtotal?: number
  tax_amount?: number
  total_amount?: number
  amount_paid?: number
  amount_due?: number
  status?: string
  due_date?: string
  customer?: { name: string }
  customer_id?: string
  [key: string]: unknown
}

export const InvoicesPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<InvoiceRecord | null>(null)
  const [formData, setFormData] = useState({
    invoice_number: '',
    invoice_type: 'receivable',
    customer_id: '',
    subtotal: 1000,
    tax_amount: 100,
    total_amount: 1100,
    status: 'sent',
    due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['invoices', page, pageSize, search],
    queryFn: () => invoiceService.list({ page, page_size: pageSize, search }),
  })

  const { data: customersData } = useQuery({
    queryKey: ['customers-select-invoices'],
    queryFn: () => customerService.list({ page_size: 100 }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      const body = {
        invoice_number: payload.invoice_number,
        invoice_type: payload.invoice_type,
        customer_id: payload.customer_id || undefined,
        subtotal: Number(payload.subtotal),
        tax_amount: Number(payload.tax_amount),
        total_amount: Number(payload.total_amount),
        status: payload.status,
        due_date: payload.due_date,
      }
      if (editingItem) return invoiceService.update(editingItem.id, body)
      return invoiceService.create(body)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Invoice updated' : 'Invoice created')
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      queryClient.invalidateQueries({ queryKey: ['reports-summary'] })
      setIsModalOpen(false)
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || err?.response?.data?.detail || 'Failed to save invoice'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => invoiceService.delete(id),
    onSuccess: () => {
      toast.success('Invoice deleted')
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      queryClient.invalidateQueries({ queryKey: ['reports-summary'] })
    },
    onError: () => toast.error('Failed to delete invoice'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    const nextNum = `INV-${Math.floor(100000 + Math.random() * 900000)}`
    setFormData({
      invoice_number: nextNum,
      invoice_type: 'receivable',
      customer_id: customersData?.items?.[0]?.id || '',
      subtotal: 1000,
      tax_amount: 100,
      total_amount: 1100,
      status: 'sent',
      due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: InvoiceRecord) => {
    setEditingItem(item)
    setFormData({
      invoice_number: item.invoice_number || '',
      invoice_type: item.invoice_type || 'receivable',
      customer_id: (item.customer_id as string) || '',
      subtotal: item.subtotal || 0,
      tax_amount: item.tax_amount || 0,
      total_amount: item.total_amount || 0,
      status: item.status || 'sent',
      due_date: item.due_date ? String(item.due_date).split('T')[0] : new Date().toISOString().split('T')[0],
    })
    setIsModalOpen(true)
  }

  const handleSubtotalChange = (subtotalVal: number) => {
    const tax = subtotalVal * 0.1
    setFormData((prev) => ({
      ...prev,
      subtotal: subtotalVal,
      tax_amount: tax,
      total_amount: subtotalVal + tax,
    }))
  }

  const columns: Column<InvoiceRecord>[] = [
    {
      key: 'invoice_number',
      header: 'Invoice #',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-sky-50 dark:bg-sky-950/50 text-sky-600 font-bold text-xs">
            <Receipt className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">
              {row.invoice_number || `INV-${row.id.slice(0, 6).toUpperCase()}`}
            </span>
            {row.customer?.name && <p className="text-[10px] text-surface-400">{row.customer.name}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'invoice_type',
      header: 'Type',
      render: (row) => (
        <Badge variant={row.invoice_type === 'payable' ? 'warning' : 'info'} className="uppercase text-[10px]">
          {row.invoice_type || 'receivable'}
        </Badge>
      ),
    },
    {
      key: 'total_amount',
      header: 'Total Value',
      render: (row) => <span className="font-extrabold text-surface-900 dark:text-surface-100">{formatCurrency(row.total_amount || 0)}</span>,
    },
    {
      key: 'status',
      header: 'Payment Status',
      render: (row) => {
        const isPaid = row.status === 'paid'
        const isOverdue = row.status === 'overdue'
        return <Badge variant={isPaid ? 'success' : isOverdue ? 'danger' : 'info'}>{row.status || 'Sent'}</Badge>
      },
    },
    { key: 'due_date', header: 'Due Date', render: (row) => (row.due_date ? formatDate(row.due_date) : '-') },
    {
      key: 'actions',
      header: 'Actions',
      className: 'text-right',
      render: (row) => (
        <div className="flex items-center justify-end gap-1">
          <Button variant="ghost" size="sm" onClick={() => handleOpenEdit(row)}>
            <Edit2 className="w-3.5 h-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-danger-600 hover:bg-danger-50 dark:hover:bg-danger-950/40"
            onClick={() => {
              if (confirm(`Delete invoice "${row.invoice_number || row.id}"?`)) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load invoices" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length
  const customerOptions = (customersData?.items || []).map((c) => ({ label: c.name, value: c.id }))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Invoices & Receivables"
        description="Commercial sales billing, customer invoices, payment collections, and aging receivables"
        icon={<Receipt className="w-5 h-5 text-teal-700" />}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Finance' },
          { label: 'Invoices' },
        ]}
        actions={
          <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
            New Invoice
          </Button>
        }
      />

      <Search value={search} onChange={setSearch} placeholder="Search invoices by number or customer..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No commercial invoices found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Invoice' : 'Create New Invoice'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input label="Invoice Number" value={formData.invoice_number} onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })} required />
          <Select
            label="Invoice Type"
            value={formData.invoice_type}
            onChange={(e) => setFormData({ ...formData, invoice_type: e.target.value })}
            options={[
              { label: 'Customer Receivable (Sales)', value: 'receivable' },
              { label: 'Vendor Payable (Purchases)', value: 'payable' },
            ]}
          />
          {customerOptions.length > 0 && (
            <Select
              label="Customer"
              value={formData.customer_id}
              onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
              options={[{ label: '-- Direct / Unassigned --', value: '' }, ...customerOptions]}
            />
          )}
          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Subtotal (₹)"
              type="number"
              step="0.01"
              value={formData.subtotal}
              onChange={(e) => handleSubtotalChange(Number(e.target.value))}
              required
            />
            <Input
              label="Tax Amount (₹)"
              type="number"
              step="0.01"
              value={formData.tax_amount}
              onChange={(e) => setFormData({ ...formData, tax_amount: Number(e.target.value), total_amount: formData.subtotal + Number(e.target.value) })}
              required
            />
            <Input
              label="Total (₹)"
              type="number"
              step="0.01"
              value={formData.total_amount}
              onChange={(e) => setFormData({ ...formData, total_amount: Number(e.target.value) })}
              required
            />
          </div>
          <Input
            label="Payment Due Date"
            type="date"
            value={formData.due_date}
            onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
            required
          />
          <Select
            label="Payment Status"
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            options={[
              { label: 'Sent / Pending', value: 'sent' },
              { label: 'Paid in Full', value: 'paid' },
              { label: 'Partially Paid', value: 'partial' },
              { label: 'Overdue', value: 'overdue' },
              { label: 'Cancelled', value: 'cancelled' },
            ]}
          />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save Invoice</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
