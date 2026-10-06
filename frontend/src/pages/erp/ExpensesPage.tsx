import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, CheckCircle, XCircle, Layers } from 'lucide-react'
import { expenseService } from '@/services/erp.service'
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
import { formatCurrency, formatDate } from '@/lib/utils'

interface ExpenseRecord {
  id: string
  title?: string
  amount: number
  category_name?: string
  status: string
  expense_date?: string
  [key: string]: unknown
}

export const ExpensesPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<ExpenseRecord | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    amount: 0,
    category_name: 'Salaries & Payroll',
    status: 'approved',
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['expenses', page, pageSize, search],
    queryFn: () => expenseService.list({ page, page_size: pageSize, search }),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      if (editingItem) return expenseService.update(editingItem.id, payload)
      return expenseService.create(payload)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Expense updated' : 'Expense recorded')
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      setIsModalOpen(false)
    },
    onError: () => toast.error('Failed to save expense'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => expenseService.delete(id),
    onSuccess: () => {
      toast.success('Expense deleted')
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
    onError: () => toast.error('Failed to delete expense'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({
      title: '',
      amount: 0,
      category_name: 'Salaries & Payroll',
      status: 'approved',
    })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: ExpenseRecord) => {
    setEditingItem(item)
    setFormData({
      title: item.title || '',
      amount: item.amount || 0,
      category_name: item.category_name || 'Salaries & Payroll',
      status: item.status || 'approved',
    })
    setIsModalOpen(true)
  }

  const columns: Column<ExpenseRecord>[] = [
    {
      key: 'title',
      header: 'Expense Details',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-rose-50 dark:bg-rose-950/50 text-rose-600 font-bold text-xs">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">{row.title || 'Expense Item'}</span>
            <p className="text-[10px] text-surface-400">{row.category_name || 'Operating Expenses'}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'amount',
      header: 'Amount',
      render: (row) => <span className="font-extrabold text-surface-900 dark:text-surface-100">{formatCurrency(row.amount || 0)}</span>,
    },
    {
      key: 'status',
      header: 'Approval Status',
      render: (row) => {
        const isApproved = row.status === 'approved'
        const isRejected = row.status === 'rejected'
        return (
          <Badge variant={isApproved ? 'success' : isRejected ? 'danger' : 'warning'} className="gap-1">
            {isApproved ? <CheckCircle className="w-3 h-3" /> : isRejected ? <XCircle className="w-3 h-3" /> : null}
            {row.status || 'Pending'}
          </Badge>
        )
      },
    },
    { key: 'expense_date', header: 'Date', render: (row) => (row.expense_date ? formatDate(row.expense_date) : '-') },
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
              if (confirm('Delete expense record?')) deleteMutation.mutate(row.id)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  if (isError) return <ErrorState title="Failed to load expenses" onRetry={() => refetch()} />

  const items = data?.items || []
  const total = data?.total || items.length

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">Operating Expenses & Claims</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Operational spend tracking, payroll, utilities, and manager approval workflows
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
          Record Expense
        </Button>
      </div>

      <Search value={search} onChange={setSearch} placeholder="Search expenses..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No expense records found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Expense Record' : 'Record Operating Expense'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input label="Expense Title / Purpose" value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} placeholder="AWS Hosting Infrastructure" required />
          <Input label="Amount ($)" type="number" step="0.01" value={formData.amount} onChange={(e) => setFormData({ ...formData, amount: Number(e.target.value) })} required />
          <Select
            label="Expense Category"
            value={formData.category_name}
            onChange={(e) => setFormData({ ...formData, category_name: e.target.value })}
            options={[
              { label: 'Salaries & Payroll', value: 'Salaries & Payroll' },
              { label: 'Rent & Real Estate Utilities', value: 'Rent & Utilities' },
              { label: 'Marketing & Ad Spend', value: 'Marketing & Growth' },
              { label: 'IT Software & Cloud Hardware', value: 'IT & Software' },
              { label: 'Logistics & Travel', value: 'Logistics & Operational' },
            ]}
          />
          <Select
            label="Approval Status"
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            options={[
              { label: 'Approved', value: 'approved' },
              { label: 'Pending Approval', value: 'pending' },
              { label: 'Rejected', value: 'rejected' },
            ]}
          />
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" isLoading={saveMutation.isPending}>Save Expense</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
