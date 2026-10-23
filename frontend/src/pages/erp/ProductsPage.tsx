import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Package } from 'lucide-react'
import { productService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Search } from '@/components/ui/Search'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { PageHeader } from '@/components/ui/PageHeader'
import { useToast } from '@/hooks/useToast'
import { formatCurrency } from '@/lib/utils'

interface ProductRecord {
  id: string
  name: string
  sku?: string
  selling_price?: number
  unit_price?: number
  cost_price?: number
  stock_quantity?: number
  reorder_level?: number
  [key: string]: unknown
}

export const ProductsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<ProductRecord | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    selling_price: 0,
    cost_price: 0,
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['products', page, pageSize, search],
    queryFn: () => productService.list({ page, page_size: pageSize, search }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      const body = {
        name: payload.name,
        sku: payload.sku,
        selling_price: payload.selling_price,
        cost_price: payload.cost_price,
      }
      if (editingItem) return productService.update(editingItem.id, body)
      return productService.create(body)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Product updated' : 'Product created')
      queryClient.invalidateQueries({ queryKey: ['products'] })
      setIsModalOpen(false)
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || err?.response?.data?.detail || 'Failed to save product'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => productService.delete(id),
    onSuccess: () => {
      toast.success('Product deleted')
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
    onError: () => toast.error('Failed to delete product'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({ name: '', sku: '', selling_price: 0, cost_price: 0 })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: ProductRecord) => {
    setEditingItem(item)
    setFormData({
      name: item.name || '',
      sku: item.sku || '',
      selling_price: item.selling_price ?? item.unit_price ?? 0,
      cost_price: item.cost_price || 0,
    })
    setIsModalOpen(true)
  }

  const columns: Column<ProductRecord>[] = [
    {
      key: 'name',
      header: 'Product Item',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary-50 dark:bg-primary-950/50 text-primary-600 font-bold text-xs">
            <Package className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">{row.name}</span>
            {row.sku && <p className="text-[10px] text-surface-400 font-mono">SKU: {row.sku}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'selling_price',
      header: 'Selling Price',
      render: (row) => formatCurrency(row.selling_price ?? row.unit_price ?? 0),
    },
    {
      key: 'cost_price',
      header: 'Cost Price',
      render: (row) => formatCurrency(row.cost_price || 0),
    },
    {
      key: 'stock_quantity',
      header: 'Stock On Hand',
      render: (row) => (
        <span
          className={`font-bold ${
            (row.stock_quantity || 0) <= (row.reorder_level || 10) ? 'text-amber-600' : 'text-emerald-600'
          }`}
        >
          {row.stock_quantity || 0} units
        </span>
      ),
    },
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
              if (confirm(`Delete product "${row.name}"?`)) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load products" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Products & Master SKUs"
        description="Product catalog, pricing tiers, unit margins, and safety reorder thresholds"
        icon={<Package className="w-5 h-5 text-teal-700" />}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Inventory' },
          { label: 'Products' },
        ]}
        actions={
          <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
            Add Product
          </Button>
        }
      />

      <Search value={search} onChange={setSearch} placeholder="Search products by SKU or name..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No catalog items found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Product' : 'Add New Product'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input label="Product Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
          <Input label="SKU / Item Code" value={formData.sku} onChange={(e) => setFormData({ ...formData, sku: e.target.value })} placeholder="SKU-1001" required />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Unit Selling Price" type="number" step="0.01" value={formData.selling_price} onChange={(e) => setFormData({ ...formData, selling_price: Number(e.target.value) })} required />
            <Input label="Unit Cost Price" type="number" step="0.01" value={formData.cost_price} onChange={(e) => setFormData({ ...formData, cost_price: Number(e.target.value) })} required />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save Product</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
