import api from '@/lib/api'
import { createCrudService } from './crud.service'
import { ApiSuccessResponse } from '@/types/api.types'
import {
  AnomalyDetectionResponse,
  BusinessHealthResponse,
  ExpensePredictionResponse,
  InventoryPredictionResponse,
  PredictionHistoryItem,
  ProfitPredictionResponse,
  RevenuePredictionResponse,
  SalesPredictionResponse,
} from '@/types/ml.types'

export const companyService = createCrudService('/api/v1/companies')
export const branchService = createCrudService('/api/v1/branches')
export const userService = createCrudService('/api/v1/users')
export const customerService = createCrudService('/api/v1/customers')
export const supplierService = createCrudService('/api/v1/suppliers')
export const categoryService = createCrudService('/api/v1/categories')
export const productService = createCrudService('/api/v1/products')
export const warehouseService = createCrudService('/api/v1/warehouses')
export const stockMovementService = createCrudService('/api/v1/stock-movements')
export const salesService = createCrudService('/api/v1/sales')
export const purchasesService = createCrudService('/api/v1/purchases')
export const paymentService = createCrudService('/api/v1/payments')

export const inventoryService = {
  ...createCrudService('/api/v1/inventory'),
  async getLowStock() {
    const response = await api.get<ApiSuccessResponse<any[]>>('/api/v1/inventory/low-stock')
    return response.data.data
  },
  async adjustStock(payload: {
    product_id: string
    warehouse_id: string
    quantity_delta?: number
    quantity_change?: number
    notes?: string
  }) {
    const delta = payload.quantity_delta ?? payload.quantity_change ?? 0
    const response = await api.post<ApiSuccessResponse<any>>('/api/v1/inventory/adjust', {
      product_id: payload.product_id,
      warehouse_id: payload.warehouse_id,
      quantity_delta: delta,
      notes: payload.notes,
    })
    return response.data.data
  },
}

export const invoiceService = {
  ...createCrudService('/api/v1/invoices'),
  async getOverdue() {
    const response = await api.get<ApiSuccessResponse<any[]>>('/api/v1/invoices/overdue')
    return response.data.data
  },
}

export const expenseService = {
  ...createCrudService('/api/v1/expenses'),
  async getPendingApproval() {
    const response = await api.get<ApiSuccessResponse<any[]>>('/api/v1/expenses/pending-approval')
    return response.data.data
  },
  async approveExpense(expenseId: string, status: 'approved' | 'rejected') {
    const response = await api.post<ApiSuccessResponse<any>>(`/api/v1/expenses/${expenseId}/approve`, { status })
    return response.data.data
  },
}

export const reportService = {
  ...createCrudService('/api/v1/reports'),
  async getSummary(branchId?: string) {
    const response = await api.get<ApiSuccessResponse<{
      total_revenue: number
      total_sales_count: number
      total_expenses: number
      net_profit: number
      inventory_count: number
      low_stock_count: number
      total_outstanding: number
      recent_sales: any[]
    }>>('/api/v1/reports/summary', {
      params: branchId ? { branch_id: branchId } : undefined,
    })
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

export interface ToolCallExecution {
  tool: string
  args: Record<string, unknown>
  summary?: string
  result?: unknown
}

export interface ChatAssistantResponse {
  message: string
  role?: string
  session_id?: string
  tools_used?: ToolCallExecution[]
  provider?: string
  model?: string
  fallback_used?: boolean
  fallback_reason?: string
}

export const mlService = {
  async predictRevenue(params?: {
    monthsAhead?: number
    modelType?: string
    branchId?: string
    historicalRevenue?: number[]
  }): Promise<RevenuePredictionResponse> {
    const response = await api.post<ApiSuccessResponse<RevenuePredictionResponse>>('/api/v1/ml/revenue/predict', {
      months_ahead: params?.monthsAhead ?? 6,
      model_type: params?.modelType ?? 'xgboost',
      branch_id: params?.branchId,
      historical_revenue: params?.historicalRevenue,
    })
    return response.data.data
  },

  async predictSales(params?: {
    entityType?: string
    modelType?: string
    monthsAhead?: number
    entityId?: string
    branchId?: string
    historicalSales?: number[]
  }): Promise<SalesPredictionResponse> {
    const response = await api.post<ApiSuccessResponse<SalesPredictionResponse>>('/api/v1/ml/sales/predict', {
      entity_type: params?.entityType ?? 'product',
      model_type: params?.modelType ?? 'xgboost',
      months_ahead: params?.monthsAhead ?? 3,
      entity_id: params?.entityId,
      branch_id: params?.branchId,
      historical_sales: params?.historicalSales,
    })
    return response.data.data
  },

  async predictInventory(params?: {
    productId?: string
    productName?: string
    currentStock?: number
    unitCost?: number
    leadTimeDays?: number
    branchId?: string
    historicalMonthlyDemand?: number[]
  }): Promise<InventoryPredictionResponse> {
    const response = await api.post<ApiSuccessResponse<InventoryPredictionResponse>>('/api/v1/ml/inventory/predict', {
      product_id: params?.productId,
      product_name: params?.productName,
      current_stock: params?.currentStock,
      unit_cost: params?.unitCost ?? 10.0,
      lead_time_days: params?.leadTimeDays ?? 14,
      branch_id: params?.branchId,
      historical_monthly_demand: params?.historicalMonthlyDemand,
    })
    return response.data.data
  },

  async predictProfit(params?: {
    projectedRevenue?: number
    branchId?: string
    historicalProfits?: number[]
    historicalRevenues?: number[]
  }): Promise<ProfitPredictionResponse> {
    const response = await api.post<ApiSuccessResponse<ProfitPredictionResponse>>('/api/v1/ml/profit/predict', {
      projected_revenue: params?.projectedRevenue,
      branch_id: params?.branchId,
      historical_profits: params?.historicalProfits,
      historical_revenues: params?.historicalRevenues,
    })
    return response.data.data
  },

  async predictExpense(params?: {
    category?: string
    modelType?: string
    monthsAhead?: number
    branchId?: string
    historicalExpenses?: number[]
  }): Promise<ExpensePredictionResponse> {
    const response = await api.post<ApiSuccessResponse<ExpensePredictionResponse>>('/api/v1/ml/expense/predict', {
      category: params?.category,
      model_type: params?.modelType ?? 'xgboost',
      months_ahead: params?.monthsAhead ?? 1,
      branch_id: params?.branchId,
      historical_expenses: params?.historicalExpenses,
    })
    return response.data.data
  },

  async predictBusinessHealth(params?: {
    revenueGrowth?: number
    profitMargin?: number
    expenseControl?: number
    inventoryTurnover?: number
    paymentCollection?: number
    branchId?: string
  }): Promise<BusinessHealthResponse> {
    const response = await api.post<ApiSuccessResponse<BusinessHealthResponse>>('/api/v1/ml/business-health/predict', {
      revenue_growth: params?.revenueGrowth,
      profit_margin: params?.profitMargin,
      expense_control: params?.expenseControl,
      inventory_turnover: params?.inventoryTurnover,
      payment_collection: params?.paymentCollection,
      branch_id: params?.branchId,
    })
    return response.data.data
  },

  async predictAnomaly(params: {
    netAmount: number
    discountPct?: number
    branchId?: string
  }): Promise<AnomalyDetectionResponse> {
    const response = await api.post<ApiSuccessResponse<AnomalyDetectionResponse>>('/api/v1/ml/anomaly/predict', {
      net_amount: params.netAmount,
      discount_pct: params.discountPct ?? 0,
      branch_id: params.branchId,
    })
    return response.data.data
  },

  async getPredictionHistory(predictionType?: string): Promise<PredictionHistoryItem[]> {
    const response = await api.get<ApiSuccessResponse<PredictionHistoryItem[]>>('/api/v1/predictions', {
      params: predictionType ? { prediction_type: predictionType } : undefined,
    })
    return response.data.data || []
  },

  async chatAssistant(message: string, context?: Record<string, unknown>): Promise<ChatAssistantResponse> {
    const response = await api.post<ApiSuccessResponse<ChatAssistantResponse>>(
      '/api/v1/chat',
      {
        message,
        context,
      },
      {
        timeout: 240000,
      }
    )
    return response.data.data
  },
}

export const importService = {
  async getSchema(entityType: string) {
    const response = await api.get<ApiSuccessResponse<any>>(`/api/v1/imports/schema/${entityType}`)
    return response.data.data
  },

  async parseFile(file: File, entityType: string, sheetName?: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('entity_type', entityType)
    if (sheetName) {
      formData.append('sheet_name', sheetName)
    }
    const response = await api.post<ApiSuccessResponse<any>>('/api/v1/imports/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data.data
  },

  async validateBatch(payload: {
    entity_type: string
    column_mapping: Record<string, string>
    rows: any[]
  }) {
    const response = await api.post<ApiSuccessResponse<any>>('/api/v1/imports/validate', payload)
    return response.data.data
  },

  async confirmBatch(payload: {
    entity_type: string
    validated_rows: any[]
    conflict_policy?: 'skip' | 'update'
    idempotency_key?: string
    file_name?: string
    source_format?: string
  }) {
    const response = await api.post<ApiSuccessResponse<any>>('/api/v1/imports/confirm', payload)
    return response.data.data
  },

  async extractPdf(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<ApiSuccessResponse<any>>('/api/v1/imports/pdf/extract', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data.data
  },

  async createPdfRecord(payload: {
    record_type: 'invoice' | 'expense'
    data: any
  }) {
    const response = await api.post<ApiSuccessResponse<any>>('/api/v1/imports/pdf/create-record', payload)
    return response.data.data
  },

  async getHistory() {
    const response = await api.get<ApiSuccessResponse<any[]>>('/api/v1/imports/history')
    return response.data.data || []
  },

  async exportErrors(rowResults: any[]) {
    const response = await api.post('/api/v1/imports/export-errors', rowResults, {
      responseType: 'blob',
    })
    const blob = new Blob([response.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'validation_errors.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  },
}

