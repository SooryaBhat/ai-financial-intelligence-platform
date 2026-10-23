import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, ShoppingCart } from 'lucide-react'
import { salesService, customerService, productService } from '@/services/erp.service'
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

interface SaleRecord {
  id: string
  sale_number?: string
  total_amount?: number
  subtotal?: number
  status?: string
  created_at?: string
  customer?: { name: string }
  customer_id?: string
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

  // Creation form state
  const [saleNumber, setSaleNumber] = useState('')
  const [customerId, setCustomerId] = useState('')
  const [selectedProductId, setSelectedProductId] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [unitPrice, setUnitPrice] = useState(0)
  const [status, setStatus] = useState('confirmed')

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['sales', page, pageSize, search],
    queryFn: () => salesService.list({ page, page_size: pageSize, search }),
  })

  const { data: customersData } = useQuery({
    queryKey: ['customers-select-sales'],
    queryFn: () => customerService.list({ page_size: 100 }),
  })

  const { data: productsData } = useQuery({
    queryKey: ['products-select-sales'],
    queryFn: () => productService.list({ page_size: 100 }),
  })

  const products = productsData?.items || []
  const customers = customersData?.items || []

  const handleProductSelect = (prodId: string) => {
    setSelectedProductId(prodId)
    const found = products.find((p) => p.id === prodId)
    if (found) {
      setUnitPrice(Number(found.selling_price ?? found.unit_price ?? 0))
    }
  }

  const calculatedTotal = quantity * unitPrice

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (editingItem) {
        return salesService.update(editingItem.id, {
          status: status as any,
        })
      }
      if (!selectedProductId && products.length > 0) {
        throw new Error('Please select a product for the sale order line item')
      }
      const payload = {
        sale_number: saleNumber || `SO-${Date.now().toString().slice(-6)}`,
        customer_id: customerId || undefined,
        subtotal: calculatedTotal,
        total_amount: calculatedTotal,
        status: status as any,
        items: [
          {
            product_id: selectedProductId || products[0]?.id,
            quantity: Math.max(1, quantity),
            unit_price: unitPrice,
            line_total: calculatedTotal,
          },
        ],
      }
      return salesService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Sale updated' : 'Sale order created')
      queryClient.invalidateQueries({ queryKey: ['sales'] })
      queryClient.invalidateQueries({ queryKey: ['reports-summary'] })
      setIsModalOpen(false)
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || err?.response?.data?.detail || err?.message || 'Failed to save sale'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => salesService.delete(id),
    onSuccess: () => {
      toast.success('Sale deleted')
      queryClient.invalidateQueries({ queryKey: ['sales'] })
      queryClient.invalidateQueries({ queryKey: ['reports-summary'] })
    },
    onError: () => toast.error('Failed to delete sale'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setSaleNumber(`SO-${Date.now().toString().slice(-6)}`)
    setCustomerId(customers[0]?.id || '')
    const firstProd = products[0]
    if (firstProd) {
      setSelectedProductId(firstProd.id)
      setUnitPrice(Number(firstProd.selling_price ?? firstProd.unit_price ?? 0))
    } else {
      setSelectedProductId('')
      setUnitPrice(0)
    }
    setQuantity(1)
    setStatus('confirmed')
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: SaleRecord) => {
    setEditingItem(item)
    setSaleNumber(item.sale_number || '')
    setCustomerId(item.customer_id || '')
    setStatus(item.status || 'confirmed')
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
        const isConfirmed = row.status === 'confirmed' || row.status === 'delivered'
        return <Badge variant={isConfirmed ? 'success' : 'warning'}>{row.status || 'Draft'}</Badge>
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
              if (confirm(`Delete sale order "${row.sale_number || row.id}"?`)) deleteMutation.mutate(row.id)
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
  const customerOptions = customers.map((c) => ({ label: c.name, value: c.id }))
  const productOptions = products.map((p) => ({
    label: `${p.name} (${formatCurrency(p.selling_price ?? p.unit_price ?? 0)})`,
    value: p.id,
  }))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sales Orders & Commercial Pipeline"
        description="Commercial sales orders, customer transactions, and order fulfillment tracking"
        icon={<ShoppingCart className="w-5 h-5 text-teal-700" />}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Commercial' },
          { label: 'Sales Orders' },
        ]}
        actions={
          <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
            New Sale Order
          </Button>
        }
      />

      <Search value={search} onChange={setSearch} placeholder="Search sales orders..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No sales orders found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Sale Order' : 'Create New Sale Order'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate() }} className="space-y-4">
          <Input label="Sale Order Number" value={saleNumber} onChange={(e) => setSaleNumber(e.target.value)} required />
          {customers.length > 0 && (
            <Select
              label="Customer"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              options={[{ label: '-- Walk-in / Direct Customer --', value: '' }, ...customerOptions]}
            />
          )}

          {!editingItem && (
            <>
              {products.length > 0 ? (
                <Select
                  label="Product Item"
                  value={selectedProductId}
                  onChange={(e) => handleProductSelect(e.target.value)}
                  options={productOptions}
                  required
                />
              ) : (
                <p className="text-xs text-amber-600 bg-amber-50 p-2 rounded">
                  No products in catalog yet. Please add a product first or seed catalog.
                </p>
              )}
              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="Quantity"
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                  required
                />
                <Input
                  label="Unit Price"
                  type="number"
                  step="0.01"
                  value={unitPrice}
                  onChange={(e) => setUnitPrice(Math.max(0, Number(e.target.value)))}
                  required
                />
              </div>
              <div className="p-3 bg-surface-50 dark:bg-surface-800 rounded-lg flex justify-between items-center text-xs">
                <span className="font-semibold text-surface-600">Computed Order Total:</span>
                <span className="text-base font-extrabold text-emerald-600">{formatCurrency(calculatedTotal)}</span>
              </div>
            </>
          )}

          <Select
            label="Order Status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            options={[
              { label: 'Confirmed', value: 'confirmed' },
              { label: 'Draft', value: 'draft' },
              { label: 'Delivered', value: 'delivered' },
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
