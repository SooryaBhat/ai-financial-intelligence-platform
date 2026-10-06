import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, CreditCard } from 'lucide-react'
import { paymentService, invoiceService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Badge } from '@/components/ui/Badge'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'
import { formatCurrency, formatDate } from '@/lib/utils'

interface PaymentRecord {
  id: string
  amount: number
  payment_method?: string
  payment_date?: string
  reference_number?: string
  invoice_id?: string
  [key: string]: unknown
}

export const PaymentsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [formData, setFormData] = useState({
    invoice_id: '',
    amount: 0,
    payment_method: 'bank_transfer',
    reference_number: '',
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['payments', page, pageSize],
    queryFn: () => paymentService.list({ page, page_size: pageSize }),
  })

  const { data: invoicesData } = useQuery({
    queryKey: ['invoices-select-payments'],
    queryFn: () => invoiceService.list({ page_size: 100 }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => paymentService.create(payload),
    onSuccess: () => {
      toast.success('Payment recorded successfully')
      queryClient.invalidateQueries({ queryKey: ['payments'] })
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to record payment'),
  })

  const handleOpenCreate = () => {
    setFormData({
      invoice_id: invoicesData?.items?.[0]?.id || '',
      amount: 500,
      payment_method: 'bank_transfer',
      reference_number: `PAY-${Math.floor(100000 + Math.random() * 900000)}`,
    })
    setIsModalOpen(true)
  }

  const columns: Column<PaymentRecord>[] = [
    {
      key: 'amount',
      header: 'Payment Received',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 font-bold text-xs">
            <CreditCard className="w-4 h-4" />
          </div>
          <div>
            <span className="font-extrabold text-surface-900 dark:text-surface-100">{formatCurrency(row.amount || 0)}</span>
            {row.reference_number && <p className="text-[10px] text-surface-400 font-mono">Ref: {row.reference_number}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'payment_method',
      header: 'Method',
      render: (row) => (
        <Badge variant="info" className="uppercase font-mono text-[10px]">
          {row.payment_method?.replace(/_/g, ' ') || 'Bank Transfer'}
        </Badge>
      ),
    },
    {
      key: 'invoice_id',
      header: 'Invoice Reference',
      render: (row) => `Invoice #${row.invoice_id?.slice(0, 8) || 'N/A'}`,
    },
    { key: 'payment_date', header: 'Date', render: (row) => (row.payment_date ? formatDate(row.payment_date) : '-') },
  ]

  if (isError) return <ErrorState title="Failed to load payments" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length
  const invoiceOptions = (invoicesData?.items || []).map((i) => ({
    label: `${i.invoice_number || i.id.slice(0, 8)} (${formatCurrency(i.total_amount || 0)})`,
    value: i.id,
  }))

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Payments & Remittances</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Record customer receipts, wire transfers, and invoice clearing entries
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          Record Payment
        </Button>
      </div>

      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No payment transactions logged." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Record Payment Receipt">
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Select label="Target Invoice" value={formData.invoice_id} onChange={(e) => setFormData({ ...formData, invoice_id: e.target.value })} options={invoiceOptions} required />
          <Input label="Payment Amount ($)" type="number" step="0.01" value={formData.amount} onChange={(e) => setFormData({ ...formData, amount: Number(e.target.value) })} required />
          <Select
            label="Payment Gateway / Method"
            value={formData.payment_method}
            onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
            options={[
              { label: 'Bank Wire Transfer', value: 'bank_transfer' },
              { label: 'Credit Card / Stripe', value: 'credit_card' },
              { label: 'ACH Direct Debit', value: 'ach' },
              { label: 'Check / Money Order', value: 'check' },
            ]}
          />
          <Input label="Transaction / Wire Reference #" value={formData.reference_number} onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })} required />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Record Receipt</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
