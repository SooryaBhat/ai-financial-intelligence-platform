import React from 'react'
import { cn } from '@/lib/utils'

interface Breadcrumb {
  label: string
  href?: string
}

export interface PageHeaderProps {
  title: string
  description?: string
  icon?: React.ReactNode
  actions?: React.ReactNode
  badge?: React.ReactNode
  breadcrumbs?: Breadcrumb[]
  className?: string
}

/**
 * Consistent enterprise page header used across all ERP module pages.
 * Provides title, optional description, icon, breadcrumb trail, and action area.
 */
export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  icon,
  actions,
  badge,
  breadcrumbs,
  className,
}) => {
  return (
    <div className={cn('page-header-bar', className)}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center gap-1.5 mb-3 text-[11px] text-slate-400 font-medium">
          {breadcrumbs.map((crumb, i) => (
            <React.Fragment key={i}>
              {i > 0 && <span className="text-slate-300">/</span>}
              {crumb.href ? (
                <a href={crumb.href} className="hover:text-teal-700 transition-colors">
                  {crumb.label}
                </a>
              ) : (
                <span className={i === breadcrumbs.length - 1 ? 'text-slate-600' : ''}>{crumb.label}</span>
              )}
            </React.Fragment>
          ))}
        </nav>
      )}

      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          {icon && (
            <div className="p-2.5 rounded-xl bg-teal-50 border border-teal-100 text-teal-700 shrink-0 mt-0.5">
              {icon}
            </div>
          )}
          <div className="min-w-0">
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight leading-tight">{title}</h1>
              {badge}
            </div>
            {description && (
              <p className="text-xs text-slate-500 mt-1 leading-relaxed max-w-2xl">{description}</p>
            )}
          </div>
        </div>

        {actions && (
          <div className="flex items-center gap-2 shrink-0">{actions}</div>
        )}
      </div>
    </div>
  )
}
