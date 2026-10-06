import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Building2 } from 'lucide-react'
import { companyService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Search } from '@/components/ui/Search'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'
import { formatDate } from '@/lib/utils'

interface CompanyRecord {
  id: string
  name: string
  slug: string
  industry?: string
  currency?: string
  created_at?: string
  [key: string]: unknown
}

export const CompaniesPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<CompanyRecord | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    industry: 'Technology',
    currency: 'USD',
  })

  // Fetch Companies list with pagination & search
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['companies', page, pageSize, search],
    queryFn: () => companyService.list({ page, page_size: pageSize, search }),
  })

  // Create / Update mutation
  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      if (editingItem) {
        return companyService.update(editingItem.id, payload)
      }
      return companyService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Company updated successfully' : 'Company created successfully')
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      handleCloseModal()
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to save company'
      toast.error(msg)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => companyService.delete(id),
    onSuccess: () => {
      toast.success('Company deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
    onError: () => toast.error('Failed to delete company'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({ name: '', slug: '', industry: 'Technology', currency: 'USD' })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: CompanyRecord) => {
    setEditingItem(item)
    setFormData({
      name: item.name || '',
      slug: item.slug || '',
      industry: item.industry || 'Technology',
      currency: item.currency || 'USD',
    })
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingItem(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name || !formData.slug) {
      toast.error('Company Name and Slug are required')
      return
    }
    saveMutation.mutate(formData)
  }

  const columns: Column<CompanyRecord>[] = [
    {
      key: 'name',
      header: 'Company Name',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary-50 dark:bg-primary-950/50 text-primary-600 font-bold text-xs">
            <Building2 className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">{row.name}</span>
            <p className="text-[10px] text-surface-400 font-mono">{row.slug}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'industry',
      header: 'Industry',
      render: (row) => row.industry || 'Technology',
    },
    {
      key: 'currency',
      header: 'Currency',
      render: (row) => (
        <span className="px-2 py-0.5 text-xs font-mono font-semibold rounded bg-surface-100 dark:bg-surface-800 text-surface-700 dark:text-surface-300">
          {row.currency || 'USD'}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Created Date',
      render: (row) => (row.created_at ? formatDate(row.created_at) : '-'),
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
            onClick={(e) => {
              e.stopPropagation()
              handleOpenEdit(row)
            }}
          >
            <Edit2 className="w-3.5 h-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-danger-600 hover:bg-danger-50 dark:hover:bg-danger-950/40"
            onClick={(e) => {
              e.stopPropagation()
              if (confirm(`Delete company "${row.name}"?`)) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) {
    return <ErrorState title="Failed to load companies" onRetry={() => refetch()} />
  }

  const items = data?.items || []
  const total = data?.total || items.length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Companies & Organizations</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Manage multi-tenant company accounts and operational parameters
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          Add Company
        </Button>
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <Search value={search} onChange={setSearch} placeholder="Search companies by name..." />
      </div>

      {/* Data Table */}
      <Table
        columns={columns}
        data={items}
        isLoading={isLoading}
        emptyText="No companies found. Click 'Add Company' to create one."
      />

      {/* Pagination */}
      <Pagination
        currentPage={page}
        totalItems={total}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Form Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingItem ? 'Edit Company' : 'Add New Company'}
        description="Provide organizational details for multi-tenant ERP operations"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Company Name"
            value={formData.name}
            onChange={(e) => {
              const val = e.target.value
              setFormData((prev) => ({
                ...prev,
                name: val,
                slug: val.toLowerCase().replace(/[^a-z0-9]/g, '-'),
              }))
            }}
            placeholder="Acme Financial Corp"
            required
          />
          <Input
            label="Company Slug"
            value={formData.slug}
            onChange={(e) => setFormData((prev) => ({ ...prev, slug: e.target.value }))}
            placeholder="acme-financial"
            required
          />
          <Select
            label="Industry"
            value={formData.industry}
            onChange={(e) => setFormData((prev) => ({ ...prev, industry: e.target.value }))}
            options={[
              { label: 'Technology', value: 'Technology' },
              { label: 'Retail & E-commerce', value: 'Retail' },
              { label: 'Manufacturing', value: 'Manufacturing' },
              { label: 'Healthcare', value: 'Healthcare' },
              { label: 'Financial Services', value: 'Financial' },
            ]}
          />
          <Select
            label="Currency"
            value={formData.currency}
            onChange={(e) => setFormData((prev) => ({ ...prev, currency: e.target.value }))}
            options={[
              { label: 'USD ($)', value: 'USD' },
              { label: 'EUR (€)', value: 'EUR' },
              { label: 'GBP (£)', value: 'GBP' },
              { label: 'CAD ($)', value: 'CAD' },
              { label: 'INR (₹)', value: 'INR' },
            ]}
          />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={handleCloseModal}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>
              {editingItem ? 'Save Changes' : 'Create Company'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
