import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Building2 } from 'lucide-react'
import { supplierService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Search } from '@/components/ui/Search'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'

interface SupplierRecord {
  id: string
  name: string
  contact_person?: string
  email?: string
  phone?: string
  address?: string
  [key: string]: unknown
}

export const SuppliersPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<SupplierRecord | null>(null)
  const [formData, setFormData] = useState({ name: '', contact_person: '', email: '', phone: '' })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['suppliers', page, pageSize, search],
    queryFn: () => supplierService.list({ page, page_size: pageSize, search }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      if (editingItem) return supplierService.update(editingItem.id, payload)
      return supplierService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Supplier updated' : 'Supplier created')
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to save supplier'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => supplierService.delete(id),
    onSuccess: () => {
      toast.success('Supplier deleted')
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
    },
    onError: () => toast.error('Failed to delete supplier'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({ name: '', contact_person: '', email: '', phone: '' })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: SupplierRecord) => {
    setEditingItem(item)
    setFormData({
      name: item.name || '',
      contact_person: item.contact_person || '',
      email: item.email || '',
      phone: item.phone || '',
    })
    setIsModalOpen(true)
  }

  const columns: Column<SupplierRecord>[] = [
    {
      key: 'name',
      header: 'Supplier Name',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-amber-50 dark:bg-amber-950/50 text-amber-600 font-bold text-xs">
            <Building2 className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">{row.name}</span>
            {row.contact_person && <p className="text-[10px] text-surface-400">Contact: {row.contact_person}</p>}
          </div>
        </div>
      ),
    },
    { key: 'email', header: 'Email', render: (row) => row.email || '-' },
    { key: 'phone', header: 'Phone', render: (row) => row.phone || '-' },
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
              if (confirm(`Delete supplier "${row.name}"?`)) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load suppliers" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Suppliers & Vendors</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Procurement vendors, wholesale suppliers, and trade contacts
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          Add Supplier
        </Button>
      </div>

      <Search value={search} onChange={setSearch} placeholder="Search suppliers..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No suppliers found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Supplier' : 'Add New Supplier'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input label="Supplier Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
          <Input label="Contact Representative" value={formData.contact_person} onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })} />
          <Input label="Email" type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} />
          <Input label="Phone" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
