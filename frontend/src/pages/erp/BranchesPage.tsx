import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, GitBranch } from 'lucide-react'
import { branchService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Search } from '@/components/ui/Search'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { PageHeader } from '@/components/ui/PageHeader'
import { useToast } from '@/hooks/useToast'

interface BranchRecord {
  id: string
  name: string
  city?: string
  country?: string
  address?: string
  phone?: string
  is_active?: boolean
  [key: string]: unknown
}

export const BranchesPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<BranchRecord | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    city: '',
    country: '',
    address: '',
    phone: '',
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['branches', page, pageSize, search],
    queryFn: () => branchService.list({ page, page_size: pageSize, search }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      const body = {
        name: payload.name,
        city: payload.city || undefined,
        country: payload.country || undefined,
        address: payload.address || undefined,
        phone: payload.phone || undefined,
      }
      if (editingItem) return branchService.update(editingItem.id, body)
      return branchService.create(body)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Branch updated' : 'Branch created')
      queryClient.invalidateQueries({ queryKey: ['branches'] })
      setIsModalOpen(false)
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || err?.response?.data?.detail || 'Failed to save branch'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => branchService.delete(id),
    onSuccess: () => {
      toast.success('Branch deleted')
      queryClient.invalidateQueries({ queryKey: ['branches'] })
    },
    onError: () => toast.error('Failed to delete branch'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({ name: '', city: '', country: '', address: '', phone: '' })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: BranchRecord) => {
    setEditingItem(item)
    setFormData({
      name: item.name || '',
      city: item.city || '',
      country: item.country || '',
      address: item.address || '',
      phone: item.phone || '',
    })
    setIsModalOpen(true)
  }

  const columns: Column<BranchRecord>[] = [
    {
      key: 'name',
      header: 'Branch Name',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 font-bold text-xs">
            <GitBranch className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">{row.name}</span>
            {(row.city || row.country) && (
              <p className="text-[10px] text-surface-400">
                {[row.city, row.country].filter(Boolean).join(', ')}
              </p>
            )}
          </div>
        </div>
      ),
    },
    { key: 'address', header: 'Address', render: (row) => row.address || '-' },
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
              if (confirm(`Delete branch "${row.name}"?`)) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load branches" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Branches & Regional Locations"
        description="Branch outlets, regional subsidiaries, and location-based business units"
        icon={<GitBranch className="w-5 h-5 text-teal-700" />}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Admin' },
          { label: 'Branches' },
        ]}
        actions={
          <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
            Add Branch
          </Button>
        }
      />

      <Search value={search} onChange={setSearch} placeholder="Search branches by location or name..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No branches registered." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Branch' : 'Add New Branch'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input label="Branch / Outlet Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
          <div className="grid grid-cols-2 gap-3">
            <Input label="City" value={formData.city} onChange={(e) => setFormData({ ...formData, city: e.target.value })} />
            <Input label="Country" value={formData.country} onChange={(e) => setFormData({ ...formData, country: e.target.value })} />
          </div>
          <Input label="Address" value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} />
          <Input label="Contact Phone" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save Branch</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
