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
import { useToast } from '@/hooks/useToast'

interface BranchRecord {
  id: string
  name: string
  code?: string
  address?: string
  phone?: string
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
  const [formData, setFormData] = useState({ name: '', code: '', address: '', phone: '' })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['branches', page, pageSize, search],
    queryFn: () => branchService.list({ page, page_size: pageSize, search }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      if (editingItem) return branchService.update(editingItem.id, payload)
      return branchService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Branch updated' : 'Branch created')
      queryClient.invalidateQueries({ queryKey: ['branches'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to save branch'),
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
    setFormData({ name: '', code: '', address: '', phone: '' })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: BranchRecord) => {
    setEditingItem(item)
    setFormData({
      name: item.name || '',
      code: item.code || '',
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
            {row.code && <p className="text-[10px] text-surface-400 font-mono">Code: {row.code}</p>}
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Branches & Locations</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Regional offices, retail stores, and operational branches
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          Add Branch
        </Button>
      </div>

      <Search value={search} onChange={setSearch} placeholder="Search branches..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No branches found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Branch' : 'Add New Branch'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input label="Branch Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
          <Input label="Branch Code" value={formData.code} onChange={(e) => setFormData({ ...formData, code: e.target.value })} placeholder="BR-001" />
          <Input label="Address" value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} />
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
