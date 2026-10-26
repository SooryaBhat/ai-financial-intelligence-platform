import React from 'react'
import { cn } from '@/lib/utils'

export type ModuleIconName =
  | 'ai-copilot-voice'
  | 'anomaly-detection'
  | 'branches'
  | 'business-health'
  | 'categories'
  | 'companies'
  | 'customers'
  | 'dashboard'
  | 'data-import'
  | 'expense-forecast'
  | 'expenses'
  | 'financial-reports'
  | 'inventory'
  | 'inventory-reorder'
  | 'invoices-billing'
  | 'notifications'
  | 'payments'
  | 'platform-settings'
  | 'products-skus'
  | 'profit-prediction'
  | 'purchase-orders'
  | 'revenue-forecast'
  | 'sales-demand'
  | 'sales-orders'
  | 'stock-movements'
  | 'suppliers'
  | 'users-roles'
  | 'warehouses'

export interface ModuleIconProps {
  name: ModuleIconName
  size?: 'xs' | 'sm' | 'nav' | 'md' | 'lg' | 'xl'
  className?: string
  alt?: string
  priority?: boolean
}

const sizeClasses = {
  xs: 'w-4 h-4',
  sm: 'w-5 h-5',
  nav: 'w-5 h-5 sm:w-5.5 sm:h-5.5',
  md: 'w-10 h-10', // 40px
  lg: 'w-11 h-11 sm:w-12 sm:h-12', // 44-48px
  xl: 'w-14 h-14', // 56px
}

/**
 * Renders an official ALLADIN colourful vector module icon from /assets/module-icons/
 */
export const ModuleIcon: React.FC<ModuleIconProps> = ({
  name,
  size = 'md',
  className,
  alt,
}) => {
  const assetPath = `/assets/module-icons/${name}.svg`

  return (
    <img
      src={assetPath}
      alt={alt || name.replace(/-/g, ' ')}
      className={cn(
        'shrink-0 object-contain select-none transition-transform duration-150',
        sizeClasses[size],
        className
      )}
      loading="lazy"
      decoding="async"
    />
  )
}

/**
 * Helper to map feature identifiers / route keys to their official 28 module SVG icons
 */
export const featureToModuleIconMap: Record<string, ModuleIconName> = {
  // Operational & Commercial
  dashboard: 'dashboard',
  overview: 'dashboard',
  imports: 'data-import',
  'data-import': 'data-import',
  sales: 'sales-orders',
  'sales-orders': 'sales-orders',
  invoices: 'invoices-billing',
  'invoices-billing': 'invoices-billing',
  customers: 'customers',
  payments: 'payments',
  expenses: 'expenses',

  // Procurement & Inventory
  products: 'products-skus',
  'products-skus': 'products-skus',
  inventory: 'inventory',
  'stock-movements': 'stock-movements',
  warehouses: 'warehouses',
  categories: 'categories',
  purchases: 'purchase-orders',
  'purchase-orders': 'purchase-orders',
  suppliers: 'suppliers',

  // ML & Forecasting Suite
  'revenue-forecast': 'revenue-forecast',
  'ml-revenue': 'revenue-forecast',
  'sales-demand': 'sales-demand',
  'ml-sales': 'sales-demand',
  'inventory-reorder': 'inventory-reorder',
  'ml-inventory': 'inventory-reorder',
  'profit-prediction': 'profit-prediction',
  'ml-profit': 'profit-prediction',
  'expense-forecast': 'expense-forecast',
  'ml-expense': 'expense-forecast',
  'business-health': 'business-health',
  'ml-business-health': 'business-health',
  'anomaly-detection': 'anomaly-detection',
  'ml-anomalies': 'anomaly-detection',
  'ai-copilot-voice': 'ai-copilot-voice',
  'ml-chat': 'ai-copilot-voice',
  copilot: 'ai-copilot-voice',

  // Organization & Admin
  companies: 'companies',
  branches: 'branches',
  users: 'users-roles',
  'users-roles': 'users-roles',
  reports: 'financial-reports',
  'financial-reports': 'financial-reports',
  notifications: 'notifications',
  settings: 'platform-settings',
  'platform-settings': 'platform-settings',
}

export const getModuleIconName = (key: string): ModuleIconName => {
  return featureToModuleIconMap[key] || 'dashboard'
}
