import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, UserCheck, Shield } from 'lucide-react'
import { userService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Badge } from '@/components/ui/Badge'
import { Table, Column } from '@/components/ui/Table'
import { Modal } from '@/components/ui/Modal'
import { Search } from '@/components/ui/Search'
import { Pagination } from '@/components/ui/Pagination'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'

interface UserRecord {
  id: string
  email: string
  full_name?: string
  role?: string
  is_active?: boolean
  [key: string]: unknown
}

export const UsersPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<UserRecord | null>(null)
  const [formData, setFormData] = useState({ full_name: '', email: '', role: 'Manager' })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['users', page, pageSize, search],
    queryFn: () => userService.list({ page, page_size: pageSize, search }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      if (editingItem) return userService.update(editingItem.id, payload)
      return userService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'User updated' : 'User invited')
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to save user'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => userService.delete(id),
    onSuccess: () => {
      toast.success('User access revoked')
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: () => toast.error('Failed to remove user'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({ full_name: '', email: '', role: 'Manager' })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: UserRecord) => {
    setEditingItem(item)
    setFormData({
      full_name: item.full_name || '',
      email: item.email || '',
      role: item.role || 'Manager',
    })
    setIsModalOpen(true)
  }

  const columns: Column<UserRecord>[] = [
    {
      key: 'full_name',
      header: 'User',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary-600 text-white font-bold text-xs flex items-center justify-center">
            {row.full_name?.charAt(0).toUpperCase() || row.email?.charAt(0).toUpperCase()}
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">{row.full_name || 'User'}</span>
            <p className="text-xs text-surface-500 dark:text-surface-400">{row.email}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      render: (row) => (
        <Badge variant="info" className="gap-1">
          <Shield className="w-3 h-3" />
          {row.role || 'Member'}
        </Badge>
      ),
    },
    {
      key: 'is_active',
      header: 'Status',
      render: (row) => (
        <Badge variant={row.is_active !== false ? 'success' : 'danger'}>
          {row.is_active !== false ? 'Active' : 'Disabled'}
        </Badge>
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
              if (confirm(`Revoke access for "${row.email}"?`)) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load users" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Users & RBAC Access</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Team members, role permissions, and administrative access
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          Invite User
        </Button>
      </div>

      <Search value={search} onChange={setSearch} placeholder="Search users by name or email..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No user accounts found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit User Role' : 'Invite New Team Member'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input label="Full Name" value={formData.full_name} onChange={(e) => setFormData({ ...formData, full_name: e.target.value })} required />
          <Input label="Email Address" type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} required />
          <Select
            label="Assigned Role"
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            options={[
              { label: 'Administrator', value: 'Admin' },
              { label: 'Financial Manager', value: 'Manager font-semibold' },
              { label: 'Accountant / Billing', value: 'Accountant' },
              { label: 'Inventory Officer', value: 'Inventory' },
              { label: 'Viewer / Auditor', value: 'Viewer' },
            ]}
          />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
