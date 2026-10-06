import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Warehouse } from 'lucide-react'
import { warehouseService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Search } from '@/components/ui/Search'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'

interface WarehouseRecord {
  id: string
  name: string
  location?: string
  capacity?: number
  manager_name?: string
  [key: string]: unknown
}

export const WarehousesPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<WarehouseRecord | null>(null)
  const [formData, setFormData] = useState({ name: '', location: '', capacity: 1000 })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['warehouses', page, pageSize, search],
    queryFn: () => warehouseService.list({ page, page_size: pageSize, search }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      if (editingItem) return warehouseService.update(editingItem.id, payload)
      return warehouseService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Warehouse updated' : 'Warehouse created')
      queryClient.invalidateQueries({ queryKey: ['warehouses'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to save warehouse'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => warehouseService.delete(id),
    onSuccess: () => {
      toast.success('Warehouse deleted')
      queryClient.invalidateQueries({ queryKey: ['warehouses'] })
    },
    onError: () => toast.error('Failed to delete warehouse'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({ name: '', location: '', capacity: 1000 })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: WarehouseRecord) => {
    setEditingItem(item)
    setFormData({
      name: item.name || '',
      location: item.location || '',
      capacity: item.capacity || 1000,
    })
    setIsModalOpen(true)
  }

  const columns: Column<WarehouseRecord>[] = [
    {
      key: 'name',
      header: 'Warehouse Facility',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 font-bold text-xs">
            <Warehouse className="w-4 h-4" />
          </div>
          <span className="font-semibold text-surface-900 dark:text-surface-100">{row.name}</span>
        </div>
      ),
    },
    { key: 'location', header: 'Location', render: (row) => row.location || '-' },
    { key: 'capacity', header: 'Storage Capacity', render: (row) => `${row.capacity || 0} units` },
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
              if (confirm(`Delete warehouse "${row.name}"?`)) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load warehouses" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Warehouses & Storage Facilities</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Physical fulfillment centers, storage bins, and holding facilities
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          Add Warehouse
        </Button>
      </div>

      <Search value={search} onChange={setSearch} placeholder="Search warehouses..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No storage warehouses found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Warehouse' : 'Add New Warehouse'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input label="Warehouse Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
          <Input label="Location Address / City" value={formData.location} onChange={(e) => setFormData({ ...formData, location: e.target.value })} />
          <Input label="Total Unit Capacity" type="number" value={formData.capacity} onChange={(e) => setFormData({ ...formData, capacity: Number(e.target.value) })} />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save Warehouse</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
