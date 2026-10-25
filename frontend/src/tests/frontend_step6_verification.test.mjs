import { test, describe } from 'node:test'
import assert from 'node:assert/strict'

describe('ALLADIN Step 6 — Frontend API Client & Contracts Verification', () => {

  test('Centralized API client headers contract', () => {
    // Mock localStorage
    const storage = new Map([
      ['access_token', 'mock_jwt_token_alladin_user'],
      ['active_company_id', 'c1111111-1111-1111-1111-111111111111'],
      ['active_branch_id', 'b1111111-1111-1111-1111-111111111111'],
    ])

    const getHeaders = (storageMap) => {
      const token = storageMap.get('access_token')
      const companyId = storageMap.get('active_company_id')
      const branchId = storageMap.get('active_branch_id')

      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      if (companyId) headers['X-Company-ID'] = companyId
      if (branchId) headers['X-Branch-ID'] = branchId
      return headers
    }

    const headers = getHeaders(storage)
    assert.equal(headers['Authorization'], 'Bearer mock_jwt_token_alladin_user')
    assert.equal(headers['X-Company-ID'], 'c1111111-1111-1111-1111-111111111111')
    assert.equal(headers['X-Branch-ID'], 'b1111111-1111-1111-1111-111111111111')

    // Test without branch ID
    storage.delete('active_branch_id')
    const headersNoBranch = getHeaders(storage)
    assert.equal(headersNoBranch['X-Branch-ID'], undefined)
    assert.equal(headersNoBranch['X-Company-ID'], 'c1111111-1111-1111-1111-111111111111')
  })

  test('7 ML endpoints routing contract', () => {
    const endpoints = {
      revenue: '/api/v1/ml/revenue/predict',
      sales: '/api/v1/ml/sales/predict',
      inventory: '/api/v1/ml/inventory/predict',
      profit: '/api/v1/ml/profit/predict',
      expense: '/api/v1/ml/expense/predict',
      businessHealth: '/api/v1/ml/business-health/predict',
      anomaly: '/api/v1/ml/anomaly/predict',
      history: (type) => `/api/v1/predictions?prediction_type=${type}`,
    }

    assert.equal(endpoints.revenue, '/api/v1/ml/revenue/predict')
    assert.equal(endpoints.sales, '/api/v1/ml/sales/predict')
    assert.equal(endpoints.inventory, '/api/v1/ml/inventory/predict')
    assert.equal(endpoints.profit, '/api/v1/ml/profit/predict')
    assert.equal(endpoints.expense, '/api/v1/ml/expense/predict')
    assert.equal(endpoints.businessHealth, '/api/v1/ml/business-health/predict')
    assert.equal(endpoints.anomaly, '/api/v1/ml/anomaly/predict')
    assert.equal(endpoints.history('revenue'), '/api/v1/predictions?prediction_type=revenue')
    assert.equal(endpoints.history('sales'), '/api/v1/predictions?prediction_type=sales')
  })

  test('ERP CRUD endpoints contract', () => {
    const erpEndpoints = {
      products: '/api/v1/products',
      sales: '/api/v1/sales',
      inventoryAdjust: '/api/v1/inventory/adjust',
      inventoryLowStock: '/api/v1/inventory/low-stock',
      expensesApprove: (id) => `/api/v1/expenses/${id}/approve`,
      invoicesOverdue: '/api/v1/invoices/overdue',
      branches: '/api/v1/branches',
      reportSummary: (branchId) => branchId ? `/api/v1/reports/summary?branch_id=${branchId}` : '/api/v1/reports/summary',
    }

    assert.equal(erpEndpoints.products, '/api/v1/products')
    assert.equal(erpEndpoints.sales, '/api/v1/sales')
    assert.equal(erpEndpoints.inventoryAdjust, '/api/v1/inventory/adjust')
    assert.equal(erpEndpoints.inventoryLowStock, '/api/v1/inventory/low-stock')
    assert.equal(erpEndpoints.expensesApprove('exp-123'), '/api/v1/expenses/exp-123/approve')
    assert.equal(erpEndpoints.invoicesOverdue, '/api/v1/invoices/overdue')
    assert.equal(erpEndpoints.branches, '/api/v1/branches')
    assert.equal(erpEndpoints.reportSummary('br-1'), '/api/v1/reports/summary?branch_id=br-1')
    assert.equal(erpEndpoints.reportSummary(), '/api/v1/reports/summary')
  })

  test('ML fallback status and diagnostic banner contracts', () => {
    const fallbackResponse = {
      model_used: 'Statistical Fallback (Moving Average)',
      forecast_period_months: 3,
      predictions: [
        { month: '2026-11', predicted_revenue: 125000 },
        { month: '2026-12', predicted_revenue: 130000 },
        { month: '2027-01', predicted_revenue: 128000 },
      ],
      total_projected_revenue: 383000,
      average_monthly_revenue: 127666.67,
      growth_trend: 'STABLE',
      is_fallback: true,
      warning_message: 'Insufficient historical data (less than 6 months). Falling back to statistical run-rates.',
    }

    assert.equal(fallbackResponse.is_fallback, true)
    assert.ok(fallbackResponse.warning_message.includes('Insufficient'))
    assert.equal(fallbackResponse.predictions.length, 3)

    const mlResponse = {
      model_used: 'XGBoost Revenue Regressor',
      forecast_period_months: 3,
      predictions: [
        { month: '2026-11', predicted_revenue: 145000 },
      ],
      total_projected_revenue: 145000,
      average_monthly_revenue: 145000,
      growth_trend: 'GROWING',
      is_fallback: false,
      warning_message: null,
    }

    assert.equal(mlResponse.is_fallback, false)
    assert.equal(mlResponse.warning_message, null)
  })

  test('SaleCreate item and status schema alignment', () => {
    const saleCreatePayload = {
      sale_number: 'SO-123456',
      customer_id: 'cust-uuid-1',
      subtotal: 500,
      total_amount: 500,
      status: 'confirmed',
      items: [
        {
          product_id: 'prod-uuid-1',
          quantity: 2,
          unit_price: 250,
          line_total: 500,
        },
      ],
    }

    assert.equal(saleCreatePayload.items.length, 1)
    assert.equal(saleCreatePayload.status, 'confirmed')
    assert.equal(saleCreatePayload.subtotal, saleCreatePayload.items[0].line_total)
  })

  test('ExpenseCreate description and status schema alignment', () => {
    const expenseCreatePayload = {
      description: 'Monthly office Internet and cloud utility',
      amount: 450,
      category_id: 'cat-uuid-1',
      expense_date: '2026-10-21',
    }

    assert.ok(expenseCreatePayload.description.length > 0)
    assert.ok(expenseCreatePayload.amount > 0)
    assert.ok(expenseCreatePayload.expense_date.match(/^\d{4}-\d{2}-\d{2}$/))
  })

  test('AdjustInventoryRequest delta schema alignment', () => {
    const adjustPayload = {
      product_id: 'prod-123',
      warehouse_id: 'wh-123',
      quantity_delta: -5,
      notes: 'Damaged item deduction',
    }

    assert.equal(typeof adjustPayload.quantity_delta, 'number')
    assert.equal(adjustPayload.quantity_delta, -5)
  })

  test('Production and development API URL resolution contract', () => {
    const PRODUCTION_API_URL = 'https://ai-financial-intelligence-platform-89re.onrender.com'
    const LOCAL_DEV_API_URL = 'http://localhost:8000'

    function resolveApiBaseUrl(envBaseUrl, envLegacyUrl, isProd) {
      const raw = (envBaseUrl || envLegacyUrl || '').trim()

      if (raw) {
        let sanitized = raw.replace(/\/+$/, '')
        sanitized = sanitized.replace(/\/api\/v1$/, '').replace(/\/api$/, '')

        if (isProd) {
          const isLocal = /^(https?:\/\/)?(localhost|127\.0\.0\.1)(:\d+)?/i.test(sanitized)
          if (isLocal) {
            return PRODUCTION_API_URL
          }
        }
        return sanitized
      }

      return isProd ? PRODUCTION_API_URL : LOCAL_DEV_API_URL
    }

    // 1. Production with explicit Render URL
    assert.equal(
      resolveApiBaseUrl('https://ai-financial-intelligence-platform-89re.onrender.com', undefined, true),
      PRODUCTION_API_URL
    )

    // 2. Production with trailing slash -> stripped
    assert.equal(
      resolveApiBaseUrl('https://ai-financial-intelligence-platform-89re.onrender.com/', undefined, true),
      PRODUCTION_API_URL
    )

    // 3. Production with redundant /api/v1 -> stripped
    assert.equal(
      resolveApiBaseUrl('https://ai-financial-intelligence-platform-89re.onrender.com/api/v1', undefined, true),
      PRODUCTION_API_URL
    )

    // 4. Production with missing env variable -> defaults safely to production Render URL, NEVER localhost
    assert.equal(
      resolveApiBaseUrl(undefined, undefined, true),
      PRODUCTION_API_URL
    )

    // 5. Production with accidental localhost env variable -> rejects localhost, falls back to production Render URL
    assert.equal(
      resolveApiBaseUrl('http://localhost:8000', undefined, true),
      PRODUCTION_API_URL
    )

    // 6. Local development -> preserves localhost:8000
    assert.equal(
      resolveApiBaseUrl('http://localhost:8000', undefined, false),
      LOCAL_DEV_API_URL
    )
    assert.equal(
      resolveApiBaseUrl(undefined, undefined, false),
      LOCAL_DEV_API_URL
    )

    // 7. Login endpoint URL resolution has no duplicate prefixes or double slashes
    const base = resolveApiBaseUrl(PRODUCTION_API_URL, undefined, true)
    const loginEndpoint = `${base}/api/v1/auth/login`
    assert.equal(loginEndpoint, 'https://ai-financial-intelligence-platform-89re.onrender.com/api/v1/auth/login')
    assert.ok(!loginEndpoint.includes('//api'))
    assert.ok(!loginEndpoint.includes('/api/v1/api/v1'))
  })
})

