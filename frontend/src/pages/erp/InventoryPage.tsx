import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, PackageCheck, AlertTriangle, ArrowUpDown } from 'lucide-react'
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
import { PageHeader } from '@/components/ui/PageHeader'
import { useToast } from '@/hooks/useToast'

interface InventoryRecord {
  id: string
  product_id: string
  warehouse_id: string
  quantity: number
  reorder_level?: number
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

  const [formData, setFormData] = useState({
    product_id: '',
    warehouse_id: '',
    quantity_delta: 0,
    reorder_level: 10,
    notes: '',
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['inventory', page, pageSize, search],
    queryFn: () => inventoryService.list({ page, page_size: pageSize, search }),
  })

  const { data: productsData } = useQuery({
    queryKey: ['products-select-inventory'],
    queryFn: () => productService.list({ page_size: 100 }),
  })

  const { data: warehousesData } = useQuery({
    queryKey: ['warehouses-select-inventory'],
    queryFn: () => warehouseService.list({ page_size: 100 }),
  })

  const products = productsData?.items || []
  const warehouses = warehousesData?.items || []

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (editingItem) {
        return inventoryService.update(editingItem.id, {
          reorder_level: formData.reorder_level,
        })
      }
      return inventoryService.adjustStock({
        product_id: formData.product_id,
        warehouse_id: formData.warehouse_id,
        quantity_delta: Number(formData.quantity_delta),
        notes: formData.notes,
      })
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Reorder threshold updated' : 'Stock adjustment applied')
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      queryClient.invalidateQueries({ queryKey: ['reports-summary'] })
      setIsModalOpen(false)
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || err?.response?.data?.detail || 'Failed to update stock'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })

  const handleOpenAdjust = (item?: InventoryRecord) => {
    if (item) {
      setEditingItem(null)
      setFormData({
        product_id: item.product_id,
        warehouse_id: item.warehouse_id,
        quantity_delta: 0,
        reorder_level: item.reorder_level || 10,
        notes: 'Physical count adjustment',
      })
    } else {
      setEditingItem(null)
      setFormData({
        product_id: products[0]?.id || '',
        warehouse_id: warehouses[0]?.id || '',
        quantity_delta: 10,
        reorder_level: 10,
        notes: 'Stock intake adjustment',
      })
    }
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: InventoryRecord) => {
    setEditingItem(item)
    setFormData({
      product_id: item.product_id || '',
      warehouse_id: item.warehouse_id || '',
      quantity_delta: 0,
      reorder_level: item.reorder_level || 10,
      notes: '',
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
              {row.product?.name || `Product: ${row.product_id?.slice(0, 8)}`}
            </span>
            {row.product?.sku && <p className="text-[10px] text-surface-400 font-mono">SKU: {row.product.sku}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'warehouse_id',
      header: 'Warehouse',
      render: (row) => row.warehouse?.name || `Warehouse: ${row.warehouse_id?.slice(0, 8)}`,
    },
    {
      key: 'quantity',
      header: 'Current Stock',
      render: (row) => {
        const isLow = row.quantity <= (row.reorder_level || 10)
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
      key: 'reorder_level',
      header: 'Reorder Point',
      render: (row) => `${row.reorder_level ?? 10} units`,
    },
    {
      key: 'actions',
      header: 'Actions',
      className: 'text-right',
      render: (row) => (
        <div className="flex items-center justify-end gap-1">
          <Button
            variant="ghost"
            size="sm"
            title="Adjust Stock Quantity"
            className="text-indigo-600 hover:bg-indigo-50"
            onClick={() => handleOpenAdjust(row)}
          >
            <ArrowUpDown className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" title="Edit Reorder Level" onClick={() => handleOpenEdit(row)}>
            <Edit2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load inventory" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length

  const productOptions = products.map((p) => ({ label: `${p.name} (${p.sku || 'SKU'})`, value: p.id }))
  const warehouseOptions = warehouses.map((w) => ({ label: w.name, value: w.id }))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Inventory & Warehouse Stock"
        description="Real-time multi-warehouse stock balances, bin locations, and automated reorder triggers"
        icon={<PackageCheck className="w-5 h-5 text-teal-700" />}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Inventory' },
          { label: 'Stock Levels' },
        ]}
        actions={
          <Button variant="primary" onClick={() => handleOpenAdjust()} leftIcon={<Plus className="w-4 h-4" />}>
            Adjust Stock
          </Button>
        }
      />

      <Search value={search} onChange={setSearch} placeholder="Search inventory..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No inventory items found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingItem ? 'Edit Reorder Level' : 'Stock Adjustment Voucher'}
      >
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate() }} className="space-y-4">
          {!editingItem ? (
            <>
              {productOptions.length > 0 && (
                <Select
                  label="Product SKU"
                  value={formData.product_id}
                  onChange={(e) => setFormData({ ...formData, product_id: e.target.value })}
                  options={productOptions}
                  required
                />
              )}
              {warehouseOptions.length > 0 && (
                <Select
                  label="Storage Warehouse"
                  value={formData.warehouse_id}
                  onChange={(e) => setFormData({ ...formData, warehouse_id: e.target.value })}
                  options={warehouseOptions}
                  required
                />
              )}
              <Input
                label="Adjustment Quantity (positive to add, negative to deduct)"
                type="number"
                value={formData.quantity_delta}
                onChange={(e) => setFormData({ ...formData, quantity_delta: Number(e.target.value) })}
                required
              />
              <Input
                label="Reason / Audit Note"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="e.g. Physical cycle count audit"
              />
            </>
          ) : (
            <Input
              label="Reorder Alert Threshold"
              type="number"
              value={formData.reorder_level}
              onChange={(e) => setFormData({ ...formData, reorder_level: Number(e.target.value) })}
              required
            />
          )}
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>
              {editingItem ? 'Update Threshold' : 'Post Adjustment'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
