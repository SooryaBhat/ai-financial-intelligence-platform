import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, ShoppingBag } from 'lucide-react'
import { purchasesService, supplierService } from '@/services/erp.service'
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

interface PurchaseRecord {
  id: string
  purchase_number?: string
  total_amount?: number
  status?: string
  created_at?: string
  supplier?: { name: string }
  [key: string]: unknown
}

export const PurchasesPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<PurchaseRecord | null>(null)
  const [formData, setFormData] = useState({
    supplier_id: '',
    total_amount: 0,
    status: 'completed',
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['purchases', page, pageSize, search],
    queryFn: () => purchasesService.list({ page, page_size: pageSize, search }),
  })

  const { data: suppliersData } = useQuery({
    queryKey: ['suppliers-select-purchases'],
    queryFn: () => supplierService.list({ page_size: 100 }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      if (editingItem) return purchasesService.update(editingItem.id, payload)
      return purchasesService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Purchase order updated' : 'Purchase order logged')
      queryClient.invalidateQueries({ queryKey: ['purchases'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to save purchase order'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => purchasesService.delete(id),
    onSuccess: () => {
      toast.success('Purchase order deleted')
      queryClient.invalidateQueries({ queryKey: ['purchases'] })
    },
    onError: () => toast.error('Failed to delete purchase order'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({
      supplier_id: suppliersData?.items?.[0]?.id || '',
      total_amount: 0,
      status: 'completed',
    })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: PurchaseRecord) => {
    setEditingItem(item)
    setFormData({
      supplier_id: (item.supplier_id as string) || '',
      total_amount: item.total_amount || 0,
      status: item.status || 'completed',
    })
    setIsModalOpen(true)
  }

  const columns: Column<PurchaseRecord>[] = [
    {
      key: 'purchase_number',
      header: 'PO #',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-amber-50 dark:bg-amber-950/50 text-amber-600 font-bold text-xs">
            <ShoppingBag className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">
              {row.purchase_number || `PO-${row.id.slice(0, 6).toUpperCase()}`}
            </span>
            {row.supplier?.name && <p className="text-[10px] text-surface-400">{row.supplier.name}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'total_amount',
      header: 'Total Cost',
      render: (row) => <span className="font-extrabold text-surface-900 dark:text-surface-100">{formatCurrency(row.total_amount || 0)}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => {
        const isReceived = row.status === 'completed' || row.status === 'received'
        return <Badge variant={isReceived ? 'success' : 'info'}>{row.status || 'Ordered'}</Badge>
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
              if (confirm('Delete purchase order?')) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load purchase orders" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length
  const supplierOptions = (suppliersData?.items || []).map((s) => ({ label: s.name, value: s.id }))

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Purchase Orders & Goods Inward</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Vendor purchase orders, raw materials procurement, and supplier fulfillment
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          New Purchase Order
        </Button>
      </div>

      <Search value={search} onChange={setSearch} placeholder="Search purchase orders..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No purchase orders found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Purchase Order' : 'Log New Purchase Order'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Select label="Supplier Vendor" value={formData.supplier_id} onChange={(e) => setFormData({ ...formData, supplier_id: e.target.value })} options={supplierOptions} required />
          <Input label="Total Amount ($)" type="number" step="0.01" value={formData.total_amount} onChange={(e) => setFormData({ ...formData, total_amount: Number(e.target.value) })} required />
          <Select
            label="Order Status"
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            options={[
              { label: 'Received & Stocked', value: 'completed' },
              { label: 'Pending Goods Receipt', value: 'pending' },
              { label: 'Draft PO', value: 'draft' },
            ]}
          />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save Purchase</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
