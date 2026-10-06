import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'

export const Breadcrumbs: React.FC = () => {
  const location = useLocation()
  const pathnames = location.pathname.split('/').filter((x) => x)

  if (pathnames.length === 0) return null

  return (
    <nav className="flex items-center gap-1 text-xs text-surface-500 dark:text-surface-400">
      <Link
        to="/dashboard"
        className="flex items-center gap-1 hover:text-surface-900 dark:hover:text-surface-100 transition-colors"
      >
        <Home className="w-3.5 h-3.5" />
      </Link>
      {pathnames.map((value, index) => {
        const to = `/${pathnames.slice(0, index + 1).join('/')}`
        const isLast = index === pathnames.length - 1
        const formattedName = value
          .replace(/-/g, ' ')
          .replace(/\b\w/g, (char) => char.toUpperCase())

        return (
          <React.Fragment key={to}>
            <ChevronRight className="w-3.5 h-3.5 text-surface-400" />
            {isLast ? (
              <span className="font-semibold text-surface-900 dark:text-surface-100">
                {formattedName}
              </span>
            ) : (
              <Link
                to={to}
                className="hover:text-surface-900 dark:hover:text-surface-100 transition-colors"
              >
                {formattedName}
              </Link>
            )}
          </React.Fragment>
        )
      })}
    </nav>
  )
}
