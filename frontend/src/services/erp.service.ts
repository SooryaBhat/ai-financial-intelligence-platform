import api from '@/lib/api'
import { createCrudService } from './crud.service'
import { ApiSuccessResponse } from '@/types/api.types'

export const companyService = createCrudService('/api/v1/companies')
export const branchService = createCrudService('/api/v1/branches')
export const userService = createCrudService('/api/v1/users')
export const customerService = createCrudService('/api/v1/customers')
export const supplierService = createCrudService('/api/v1/suppliers')
export const categoryService = createCrudService('/api/v1/categories')
export const productService = createCrudService('/api/v1/products')
export const warehouseService = createCrudService('/api/v1/warehouses')
export const inventoryService = createCrudService('/api/v1/inventory')
export const stockMovementService = createCrudService('/api/v1/stock-movements')
export const salesService = createCrudService('/api/v1/sales')
export const purchasesService = createCrudService('/api/v1/purchases')
export const invoiceService = createCrudService('/api/v1/invoices')
export const paymentService = createCrudService('/api/v1/payments')
export const expenseService = createCrudService('/api/v1/expenses')
export const reportService = {
  ...createCrudService('/api/v1/reports'),
  async getSummary() {
    const response = await api.get<ApiSuccessResponse<{
      total_revenue: number
      total_sales_count: number
      total_expenses: number
      net_profit: number
      inventory_count: number
      low_stock_count: number
      total_outstanding: number
      recent_sales: any[]
    }>>('/api/v1/reports/summary')
    return response.data.data
  },
}

export const notificationService = {
  async list(unreadOnly = false) {
    const response = await api.get<ApiSuccessResponse<unknown[]>>('/api/v1/notifications', {
      params: { unread_only: unreadOnly },
    })
    return response.data.data
  },
  async getUnreadCount() {
    const response = await api.get<ApiSuccessResponse<{ count: number }>>('/api/v1/notifications/unread-count')
    return response.data.data.count
  },
  async markRead(ids: string[]) {
    const response = await api.post<ApiSuccessResponse<unknown>>('/api/v1/notifications/mark-read', {
      notification_ids: ids,
    })
    return response.data.data
  },
}

export const settingService = {
  async listAll() {
    const response = await api.get<ApiSuccessResponse<Record<string, unknown>>>('/api/v1/settings')
    return response.data.data
  },
  async getByKey(key: string) {
    const response = await api.get<ApiSuccessResponse<unknown>>(`/api/v1/settings/${key}`)
    return response.data.data
  },
  async upsert(key: string, value: unknown, description?: string) {
    const response = await api.put<ApiSuccessResponse<unknown>>(`/api/v1/settings/${key}`, {
      value,
      description,
    })
    return response.data.data
  },
}

export const mlService = {
  async predictRevenue(monthsAhead = 6, modelType = 'xgboost', historicalRevenue?: number[]) {
    const response = await api.post<ApiSuccessResponse<unknown>>('/api/ml/revenue/predict', {
      months_ahead: monthsAhead,
      model_type: modelType,
      historical_revenue: historicalRevenue,
    })
    return response.data.data
  },

  async predictSales(entityType = 'product', modelType = 'xgboost', monthsAhead = 3, entityId?: string) {
    const response = await api.post<ApiSuccessResponse<unknown>>('/api/ml/sales/predict', {
      entity_type: entityType,
      model_type: modelType,
      months_ahead: monthsAhead,
      entity_id: entityId,
    })
    return response.data.data
  },

  async predictInventory(productName = 'Premium Laptop X1', currentStock = 25, unitCost = 450, leadTimeDays = 14) {
    const response = await api.post<ApiSuccessResponse<unknown>>('/api/ml/inventory/predict', {
      product_name: productName,
      current_stock: currentStock,
      unit_cost: unitCost,
      lead_time_days: leadTimeDays,
    })
    return response.data.data
  },

  async predictProfit(projectedRevenue = 22000000, historicalProfits?: number[]) {
    const response = await api.post<ApiSuccessResponse<unknown>>('/api/ml/profit/predict', {
      projected_revenue: projectedRevenue,
      historical_profits: historicalProfits,
    })
    return response.data.data
  },

  async predictExpense(category = 'Salaries', modelType = 'xgboost', monthsAhead = 1) {
    const response = await api.post<ApiSuccessResponse<unknown>>('/api/ml/expense/predict', {
      category: category,
      model_type: modelType,
      months_ahead: monthsAhead,
    })
    return response.data.data
  },

  async predictBusinessHealth(metrics?: Record<string, number>) {
    const response = await api.post<ApiSuccessResponse<unknown>>('/api/ml/business-health/predict', metrics || {})
    return response.data.data
  },

  async predictAnomaly(netAmount: number, discountPct = 0) {
    const response = await api.post<ApiSuccessResponse<unknown>>('/api/ml/anomaly/predict', {
      net_amount: netAmount,
      discount_pct: discountPct,
    })
    return response.data.data
  },

  async chatAssistant(message: string, context?: Record<string, unknown>) {
    const response = await api.post<ApiSuccessResponse<{ message: string; data?: unknown }>>('/api/v1/chat', {
      message,
      context,
    })
    return response.data.data
  },
}
