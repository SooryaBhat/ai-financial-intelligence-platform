import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Tag } from 'lucide-react'
import { categoryService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Search } from '@/components/ui/Search'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'

interface CategoryRecord {
  id: string
  name: string
  description?: string
  [key: string]: unknown
}

export const CategoriesPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<CategoryRecord | null>(null)
  const [formData, setFormData] = useState({ name: '', description: '' })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['categories', page, pageSize, search],
    queryFn: () => categoryService.list({ page, page_size: pageSize, search }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      if (editingItem) return categoryService.update(editingItem.id, payload)
      return categoryService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Category updated' : 'Category created')
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to save category'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => categoryService.delete(id),
    onSuccess: () => {
      toast.success('Category deleted')
      queryClient.invalidateQueries({ queryKey: ['categories'] })
    },
    onError: () => toast.error('Failed to delete category'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({ name: '', description: '' })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: CategoryRecord) => {
    setEditingItem(item)
    setFormData({
      name: item.name || '',
      description: item.description || '',
    })
    setIsModalOpen(true)
  }

  const columns: Column<CategoryRecord>[] = [
    {
      key: 'name',
      header: 'Category Name',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-sky-50 dark:bg-sky-950/50 text-sky-600 font-bold text-xs">
            <Tag className="w-4 h-4" />
          </div>
          <span className="font-semibold text-surface-900 dark:text-surface-100">{row.name}</span>
        </div>
      ),
    },
    { key: 'description', header: 'Description', render: (row) => row.description || '-' },
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
              if (confirm(`Delete category "${row.name}"?`)) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load categories" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Product Categories</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Group products by taxonomy, industry sectors, and catalog tags
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          Add Category
        </Button>
      </div>

      <Search value={search} onChange={setSearch} placeholder="Search categories..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No categories found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Category' : 'Add New Category'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input label="Category Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
          <Input label="Description" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
