import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, PackageCheck, AlertTriangle } from 'lucide-react'
import { inventoryService, productService, warehouseService } from '@/services/erp.service'
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

interface InventoryRecord {
  id: string
  product_id: string
  warehouse_id: string
  quantity: number
  reorder_point?: number
  product?: { name: string; sku: string }
  warehouse?: { name: string }
  [key: string]: unknown
}

export const InventoryPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<InventoryRecord | null>(null)
  const [formData, setFormData] = useState({ product_id: '', warehouse_id: '', quantity: 0, reorder_point: 10 })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['inventory', page, pageSize, search],
    queryFn: () => inventoryService.list({ page, page_size: pageSize, search }),
  })

  const { data: productsData } = useQuery({
    queryKey: ['products-select'],
    queryFn: () => productService.list({ page_size: 100 }),
  })

  const { data: warehousesData } = useQuery({
    queryKey: ['warehouses-select'],
    queryFn: () => warehouseService.list({ page_size: 100 }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      if (editingItem) return inventoryService.update(editingItem.id, payload)
      return inventoryService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Stock level updated' : 'Stock record added')
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to update inventory'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({
      product_id: productsData?.items?.[0]?.id || '',
      warehouse_id: warehousesData?.items?.[0]?.id || '',
      quantity: 0,
      reorder_point: 10,
    })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: InventoryRecord) => {
    setEditingItem(item)
    setFormData({
      product_id: item.product_id || '',
      warehouse_id: item.warehouse_id || '',
      quantity: item.quantity || 0,
      reorder_point: item.reorder_point || 10,
    })
    setIsModalOpen(true)
  }

  const columns: Column<InventoryRecord>[] = [
    {
      key: 'product_id',
      header: 'Product',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 font-bold text-xs">
            <PackageCheck className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">
              {row.product?.name || `Product ID: ${row.product_id?.slice(0, 8)}`}
            </span>
            {row.product?.sku && <p className="text-[10px] text-surface-400 font-mono">SKU: {row.product.sku}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'warehouse_id',
      header: 'Warehouse',
      render: (row) => row.warehouse?.name || `Warehouse ID: ${row.warehouse_id?.slice(0, 8)}`,
    },
    {
      key: 'quantity',
      header: 'Current Stock',
      render: (row) => {
        const isLow = row.quantity <= (row.reorder_point || 10)
        return (
          <div className="flex items-center gap-2">
            <span className={`font-bold ${isLow ? 'text-amber-600' : 'text-emerald-600'}`}>{row.quantity} units</span>
            {isLow && (
              <Badge variant="warning" className="gap-1">
                <AlertTriangle className="w-3 h-3" />
                Low Stock
              </Badge>
            )}
          </div>
        )
      },
    },
    {
      key: 'actions',
      header: 'Actions',
      className: 'text-right',
      render: (row) => (
        <Button variant="ghost" size="sm" onClick={() => handleOpenEdit(row)}>
          <Edit2 className="w-3.5 h-3.5" />
        </Button>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load inventory" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length

  const productOptions = (productsData?.items || []).map((p) => ({ label: `${p.name} (${p.sku})`, value: p.id }))
  const warehouseOptions = (warehousesData?.items || []).map((w) => ({ label: w.name, value: w.id }))

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Inventory & Stock Tracking</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Real-time multi-warehouse stock balances and automated reorder alerts
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          Adjust Stock
        </Button>
      </div>

      <Search value={search} onChange={setSearch} placeholder="Search inventory..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No inventory items found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Stock Level' : 'Add Inventory Item'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Select label="Product SKU" value={formData.product_id} onChange={(e) => setFormData({ ...formData, product_id: e.target.value })} options={productOptions} required />
          <Select label="Storage Warehouse" value={formData.warehouse_id} onChange={(e) => setFormData({ ...formData, warehouse_id: e.target.value })} options={warehouseOptions} required />
          <Input label="Quantity on Hand" type="number" value={formData.quantity} onChange={(e) => setFormData({ ...formData, quantity: Number(e.target.value) })} required />
          <Input label="Reorder Point Threshold" type="number" value={formData.reorder_point} onChange={(e) => setFormData({ ...formData, reorder_point: Number(e.target.value) })} />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save Stock</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
