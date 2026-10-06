import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, ShoppingCart } from 'lucide-react'
import { salesService, customerService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Badge } from '@/components/ui/Badge'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Search } from '@/components/ui/Search'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'
import { formatCurrency, formatDate } from '@/lib/utils'

interface SaleRecord {
  id: string
  sale_number?: string
  total_amount?: number
  status?: string
  created_at?: string
  customer?: { name: string }
  [key: string]: unknown
}

export const SalesPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<SaleRecord | null>(null)
  const [formData, setFormData] = useState({
    customer_id: '',
    total_amount: 0,
    status: 'completed',
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['sales', page, pageSize, search],
    queryFn: () => salesService.list({ page, page_size: pageSize, search }),
  })

  const { data: customersData } = useQuery({
    queryKey: ['customers-select-sales'],
    queryFn: () => customerService.list({ page_size: 100 }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      if (editingItem) return salesService.update(editingItem.id, payload)
      return salesService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Sale updated' : 'Sale order created')
      queryClient.invalidateQueries({ queryKey: ['sales'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to save sale'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => salesService.delete(id),
    onSuccess: () => {
      toast.success('Sale deleted')
      queryClient.invalidateQueries({ queryKey: ['sales'] })
    },
    onError: () => toast.error('Failed to delete sale'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({
      customer_id: customersData?.items?.[0]?.id || '',
      total_amount: 0,
      status: 'completed',
    })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: SaleRecord) => {
    setEditingItem(item)
    setFormData({
      customer_id: (item.customer_id as string) || '',
      total_amount: item.total_amount || 0,
      status: item.status || 'completed',
    })
    setIsModalOpen(true)
  }

  const columns: Column<SaleRecord>[] = [
    {
      key: 'sale_number',
      header: 'Order #',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 font-bold text-xs">
            <ShoppingCart className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">
              {row.sale_number || `SO-${row.id.slice(0, 6).toUpperCase()}`}
            </span>
            {row.customer?.name && <p className="text-[10px] text-surface-400">{row.customer.name}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'total_amount',
      header: 'Total Amount',
      render: (row) => <span className="font-extrabold text-surface-900 dark:text-surface-100">{formatCurrency(row.total_amount || 0)}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => {
        const isCompleted = row.status === 'completed'
        return <Badge variant={isCompleted ? 'success' : 'warning'}>{row.status || 'Pending'}</Badge>
      },
    },
    { key: 'created_at', header: 'Date', render: (row) => (row.created_at ? formatDate(row.created_at) : '-') },
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
              if (confirm('Delete sale order?')) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load sales" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length
  const customerOptions = (customersData?.items || []).map((c) => ({ label: c.name, value: c.id }))

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Sales Orders & Commercial Revenue</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Commercial sales orders, customer transactions, and order fulfillment
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          New Sale Order
        </Button>
      </div>

      <Search value={search} onChange={setSearch} placeholder="Search sales orders..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No sales orders found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Sale Order' : 'Create New Sale Order'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Select label="Customer" value={formData.customer_id} onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })} options={customerOptions} required />
          <Input label="Total Amount ($)" type="number" step="0.01" value={formData.total_amount} onChange={(e) => setFormData({ ...formData, total_amount: Number(e.target.value) })} required />
          <Select
            label="Order Status"
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            options={[
              { label: 'Completed', value: 'completed' },
              { label: 'Pending Fulfillment', value: 'pending' },
              { label: 'Cancelled', value: 'cancelled' },
            ]}
          />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save Sale</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
