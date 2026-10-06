export type SortDirection = 'asc' | 'desc'
export type Status = 'active' | 'inactive' | 'pending' | 'cancelled'
export type Theme = 'light' | 'dark' | 'system'

export interface SelectOption {
  label: string
  value: string
}

export interface TableColumn<T = Record<string, unknown>> {
  key: keyof T | string
  header: string
  render?: (row: T) => React.ReactNode
  sortable?: boolean
  width?: string
  align?: 'left' | 'center' | 'right'
}

export interface NavItem {
  label: string
  href: string
  icon?: React.ComponentType<{ className?: string }>
  badge?: string | number
  children?: NavItem[]
}

export interface BreadcrumbItem {
  label: string
  href?: string
}
