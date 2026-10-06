import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Users, Mail, Phone } from 'lucide-react'
import { customerService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Search } from '@/components/ui/Search'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'

interface CustomerRecord {
  id: string
  name: string
  email?: string
  phone?: string
  company_name?: string
  credit_limit?: number
  [key: string]: unknown
}

export const CustomersPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<CustomerRecord | null>(null)
  const [formData, setFormData] = useState({ name: '', email: '', phone: '', company_name: '' })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['customers', page, pageSize, search],
    queryFn: () => customerService.list({ page, page_size: pageSize, search }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      if (editingItem) return customerService.update(editingItem.id, payload)
      return customerService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Customer updated' : 'Customer created')
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to save customer'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => customerService.delete(id),
    onSuccess: () => {
      toast.success('Customer removed')
      queryClient.invalidateQueries({ queryKey: ['customers'] })
    },
    onError: () => toast.error('Failed to delete customer'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({ name: '', email: '', phone: '', company_name: '' })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: CustomerRecord) => {
    setEditingItem(item)
    setFormData({
      name: item.name || '',
      email: item.email || '',
      phone: item.phone || '',
      company_name: item.company_name || '',
    })
    setIsModalOpen(true)
  }

  const columns: Column<CustomerRecord>[] = [
    {
      key: 'name',
      header: 'Customer Name',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 font-bold text-xs">
            <Users className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">{row.name}</span>
            {row.company_name && <p className="text-[10px] text-surface-400">{row.company_name}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'email',
      header: 'Contact Info',
      render: (row) => (
        <div className="text-xs space-y-0.5">
          {row.email && (
            <div className="flex items-center gap-1.5 text-surface-600 dark:text-surface-400">
              <Mail className="w-3 h-3 text-surface-400" />
              <span>{row.email}</span>
            </div>
          )}
          {row.phone && (
            <div className="flex items-center gap-1.5 text-surface-500">
              <Phone className="w-3 h-3 text-surface-400" />
              <span>{row.phone}</span>
            </div>
          )}
        </div>
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
              if (confirm(`Delete customer "${row.name}"?`)) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load customers" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Customers & Clients</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Customer directory, credit limits, and invoicing details
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          Add Customer
        </Button>
      </div>

      <Search value={search} onChange={setSearch} placeholder="Search customers..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No customer accounts found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Customer' : 'Add New Customer'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input label="Customer / Company Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
          <Input label="Business Email" type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} />
          <Input label="Phone Number" type="tel" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} />
          <Input label="Company Name" value={formData.company_name} onChange={(e) => setFormData({ ...formData, company_name: e.target.value })} />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save Customer</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
