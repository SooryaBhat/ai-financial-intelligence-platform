import React from 'react'
import { cn } from '@/lib/utils'
import { Skeleton } from './Skeleton'

export interface Column<T> {
  key: string
  header: string
  render?: (row: T, index: number) => React.ReactNode
  className?: string
}

export interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  isLoading?: boolean
  emptyText?: string
  onRowClick?: (row: T) => void
  keyExtractor?: (row: T, index: number) => string | number
}

export function Table<T>({
  columns,
  data,
  isLoading = false,
  emptyText = 'No data available',
  onRowClick,
  keyExtractor,
}: TableProps<T>) {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 shadow-card">
      <table className="w-full text-left text-sm border-collapse">
        <thead className="bg-surface-50 dark:bg-surface-800/60 border-b border-surface-200 dark:border-surface-800 text-surface-600 dark:text-surface-400 font-medium text-xs uppercase tracking-wider">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className={cn('px-4 py-3.5', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-100 dark:divide-surface-800/60 text-surface-900 dark:text-surface-100">
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <tr key={i}>
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-4">
                    <Skeleton className="h-4 w-full" />
                  </td>
                ))}
              </tr>
            ))
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-12 text-center text-surface-400">
                {emptyText}
              </td>
            </tr>
          ) : (
            data.map((row, index) => (
              <tr
                key={keyExtractor ? keyExtractor(row, index) : index}
                onClick={() => onRowClick && onRowClick(row)}
                className={cn(
                  'transition-colors hover:bg-surface-50/80 dark:hover:bg-surface-800/40',
                  onRowClick && 'cursor-pointer'
                )}
              >
                {columns.map((col) => (
                  <td key={col.key} className={cn('px-4 py-3.5', col.className)}>
                    {col.render
                      ? col.render(row, index)
                      : String((row as Record<string, unknown>)[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
