import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, ArrowLeftRight } from 'lucide-react'
import { stockMovementService, productService, warehouseService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Badge } from '@/components/ui/Badge'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'
import { formatDate } from '@/lib/utils'

interface StockMovementRecord {
  id: string
  movement_type: 'IN' | 'OUT' | 'TRANSFER'
  quantity: number
  reference?: string
  created_at?: string
  product_id?: string
  product?: { name: string; sku: string }
  [key: string]: unknown
}

export const StockMovementsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [formData, setFormData] = useState({
    product_id: '',
    warehouse_id: '',
    movement_type: 'IN',
    quantity: 1,
    reference: '',
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['stock-movements', page, pageSize],
    queryFn: () => stockMovementService.list({ page, page_size: pageSize }),
  })

  const { data: productsData } = useQuery({
    queryKey: ['products-select-sm'],
    queryFn: () => productService.list({ page_size: 100 }),
  })

  const { data: warehousesData } = useQuery({
    queryKey: ['warehouses-select-sm'],
    queryFn: () => warehouseService.list({ page_size: 100 }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => stockMovementService.create(payload),
    onSuccess: () => {
      toast.success('Stock movement logged')
      queryClient.invalidateQueries({ queryKey: ['stock-movements'] })
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to log movement'),
  })

  const handleOpenCreate = () => {
    setFormData({
      product_id: productsData?.items?.[0]?.id || '',
      warehouse_id: warehousesData?.items?.[0]?.id || '',
      movement_type: 'IN',
      quantity: 1,
      reference: 'MANUAL-ADJ',
    })
    setIsModalOpen(true)
  }

  const columns: Column<StockMovementRecord>[] = [
    {
      key: 'movement_type',
      header: 'Type',
      render: (row) => {
        const isIn = row.movement_type === 'IN'
        const isTransfer = row.movement_type === 'TRANSFER'
        return (
          <Badge variant={isIn ? 'success' : isTransfer ? 'info' : 'danger'} className="gap-1 font-bold">
            <ArrowLeftRight className="w-3 h-3" />
            {row.movement_type}
          </Badge>
        )
      },
    },
    {
      key: 'product_id',
      header: 'Item',
      render: (row) => row.product?.name || `Product ID: ${row.product_id?.slice(0, 8)}`,
    },
    { key: 'quantity', header: 'Quantity', render: (row) => `${row.quantity} units` },
    { key: 'reference', header: 'Reference', render: (row) => row.reference || '-' },
    { key: 'created_at', header: 'Timestamp', render: (row) => (row.created_at ? formatDate(row.created_at) : '-') },
  ]

  if (isError) return <ErrorState title="Failed to load stock movements" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length

  const productOptions = (productsData?.items || []).map((p) => ({ label: p.name, value: p.id }))
  const warehouseOptions = (warehousesData?.items || []).map((w) => ({ label: w.name, value: w.id }))

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Stock Movements Audit Log</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Audit trail of goods receipts, sales dispatches, and warehouse transfers
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          Log Movement
        </Button>
      </div>

      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No stock movement records found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Log Stock Movement">
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Select label="Product SKU" value={formData.product_id} onChange={(e) => setFormData({ ...formData, product_id: e.target.value })} options={productOptions} required />
          <Select label="Warehouse Location" value={formData.warehouse_id} onChange={(e) => setFormData({ ...formData, warehouse_id: e.target.value })} options={warehouseOptions} required />
          <Select
            label="Movement Type"
            value={formData.movement_type}
            onChange={(e) => setFormData({ ...formData, movement_type: e.target.value as 'IN' | 'OUT' | 'TRANSFER' })}
            options={[
              { label: 'Stock IN (Receipt / Purchase)', value: 'IN' },
              { label: 'Stock OUT (Sale / Dispatch)', value: 'OUT' },
              { label: 'Stock TRANSFER (Relocation)', value: 'TRANSFER' },
            ]}
          />
          <Input label="Quantity" type="number" value={formData.quantity} onChange={(e) => setFormData({ ...formData, quantity: Number(e.target.value) })} required />
          <Input label="Audit Reference / PO#" value={formData.reference} onChange={(e) => setFormData({ ...formData, reference: e.target.value })} placeholder="PO-99102" />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Submit Movement</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
