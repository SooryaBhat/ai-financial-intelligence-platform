import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, CheckCircle, XCircle, Layers } from 'lucide-react'
import { expenseService, categoryService } from '@/services/erp.service'
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

interface ExpenseRecord {
  id: string
  description: string
  title?: string
  amount: number
  category_id?: string
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
    description: '',
    amount: 0,
    category_id: '',
    expense_date: new Date().toISOString().split('T')[0],
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['expenses', page, pageSize, search],
    queryFn: () => expenseService.list({ page, page_size: pageSize, search }),
  })

  const { data: categoriesData } = useQuery({
    queryKey: ['categories-select-expenses'],
    queryFn: () => categoryService.list({ page_size: 100 }),
  })

  const categories = categoriesData?.items || []

  const saveMutation = useMutation({
    mutationFn: (payload: typeof formData) => {
      const body = {
        description: payload.description,
        amount: Math.max(0.01, Number(payload.amount)),
        category_id: payload.category_id || undefined,
        expense_date: payload.expense_date,
      }
      if (editingItem) return expenseService.update(editingItem.id, body)
      return expenseService.create(body)
    },
    onSuccess: () => {
      toast.success(editingItem ? 'Expense updated' : 'Expense recorded')
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['reports-summary'] })
      setIsModalOpen(false)
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || err?.response?.data?.detail || 'Failed to save expense'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })

  const approveMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'approved' | 'rejected' }) =>
      expenseService.approveExpense(id, status),
    onSuccess: (_, vars) => {
      toast.success(`Expense ${vars.status}`)
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['reports-summary'] })
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || err?.response?.data?.detail || 'Approval failed'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => expenseService.delete(id),
    onSuccess: () => {
      toast.success('Expense deleted')
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['reports-summary'] })
    },
    onError: () => toast.error('Failed to delete expense'),
  })

  const handleOpenCreate = () => {
    setEditingItem(null)
    setFormData({
      description: '',
      amount: 0,
      category_id: categories[0]?.id || '',
      expense_date: new Date().toISOString().split('T')[0],
    })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (item: ExpenseRecord) => {
    setEditingItem(item)
    setFormData({
      description: item.description || item.title || '',
      amount: item.amount || 0,
      category_id: (item.category_id as string) || '',
      expense_date: item.expense_date ? String(item.expense_date).split('T')[0] : new Date().toISOString().split('T')[0],
    })
    setIsModalOpen(true)
  }

  const columns: Column<ExpenseRecord>[] = [
    {
      key: 'description',
      header: 'Expense Details',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-rose-50 dark:bg-rose-950/50 text-rose-600 font-bold text-xs">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-surface-900 dark:text-surface-100">{row.description || row.title || 'Expense Voucher'}</span>
            {row.category_name && <p className="text-[10px] text-surface-400">{row.category_name}</p>}
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
          {row.status === 'pending' && (
            <>
              <Button
                variant="ghost"
                size="sm"
                title="Approve Voucher"
                className="text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/40"
                onClick={() => approveMutation.mutate({ id: row.id, status: 'approved' })}
              >
                <CheckCircle className="w-3.5 h-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                title="Reject Voucher"
                className="text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                onClick={() => approveMutation.mutate({ id: row.id, status: 'rejected' })}
              >
                <XCircle className="w-3.5 h-3.5" />
              </Button>
            </>
          )}
          <Button variant="ghost" size="sm" onClick={() => handleOpenEdit(row)}>
            <Edit2 className="w-3.5 h-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-danger-600 hover:bg-danger-50 dark:hover:bg-danger-950/40"
            onClick={() => {
              if (confirm(`Delete expense "${row.description || row.title || row.id}"?`)) deleteMutation.mutate(row.id)
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
  const categoryOptions = categories.map((c) => ({ label: c.name, value: c.id }))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Operating Expenses & Vouchers"
        description="Expense vouchers, departmental cost tracking, approvals, and budget burn monitoring"
        icon={<Layers className="w-5 h-5 text-teal-700" />}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Finance' },
          { label: 'Expenses' },
        ]}
        actions={
          <Button variant="primary" onClick={handleOpenCreate} leftIcon={<Plus className="w-4 h-4" />}>
            Record Expense
          </Button>
        }
      />

      <Search value={search} onChange={setSearch} placeholder="Search expense vouchers..." />
      <Table columns={columns} data={items} isLoading={isLoading} emptyText="No expense records found." />
      <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem ? 'Edit Expense' : 'Record Operating Expense'}>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(formData) }} className="space-y-4">
          <Input
            label="Expense Description / Purpose"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="e.g. AWS Cloud Infrastructure Hosting"
            required
          />
          <Input
            label="Amount"
            type="number"
            step="0.01"
            min="0.01"
            value={formData.amount}
            onChange={(e) => setFormData({ ...formData, amount: Number(e.target.value) })}
            required
          />
          {categoryOptions.length > 0 && (
            <Select
              label="Expense Category"
              value={formData.category_id}
              onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
              options={[{ label: '-- Select Category --', value: '' }, ...categoryOptions]}
            />
          )}
          <Input
            label="Expense Date"
            type="date"
            value={formData.expense_date}
            onChange={(e) => setFormData({ ...formData, expense_date: e.target.value })}
            required
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
