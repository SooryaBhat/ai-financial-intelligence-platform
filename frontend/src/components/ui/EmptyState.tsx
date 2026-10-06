import React from 'react'
import { FolderOpen } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 text-center rounded-xl border border-dashed border-surface-200 dark:border-surface-800 bg-surface-50/50 dark:bg-surface-900/50 my-4',
        className
      )}
    >
      <div className="p-3 rounded-full bg-surface-100 dark:bg-surface-800 text-surface-400 dark:text-surface-500 mb-3">
        {icon || <FolderOpen className="w-8 h-8" />}
      </div>
      <h3 className="text-base font-semibold text-surface-900 dark:text-surface-100">{title}</h3>
      {description && (
        <p className="text-xs text-surface-500 dark:text-surface-400 max-w-sm mt-1 mb-4">
          {description}
        </p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
