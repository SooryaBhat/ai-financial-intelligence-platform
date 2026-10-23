/**
 * Typed Machine Learning Request & Response contracts aligned with FastAPI backend schemas.
 */

export interface RevenueForecastItem {
  month: string
  predicted_revenue: number
  confidence_lower: number
  confidence_upper: number
}

export interface RevenuePredictionResponse {
  model_used: string
  forecast_period_months: number
  predictions: RevenueForecastItem[]
  total_projected_revenue: number
  average_monthly_revenue: number
  growth_trend: string
  is_fallback?: boolean
  warning_message?: string | null
}

export interface SalesForecastItem {
  month: string
  predicted_units_sold: number
  predicted_sales_amount: number
}

export interface SalesPredictionResponse {
  entity_type: string
  entity_id?: string | null
  model_used: string
  predictions: SalesForecastItem[]
  total_predicted_units: number
  total_predicted_amount: number
  is_fallback?: boolean
  warning_message?: string | null
}

export interface InventoryPredictionResponse {
  product_id?: string | null
  product_name?: string | null
  current_stock: number
  predicted_monthly_demand: number
  recommended_reorder_point: number
  recommended_reorder_quantity: number
  stockout_risk_level: string
  days_of_supply_remaining: number
  reorder_recommended: boolean
  is_fallback?: boolean
  warning_message?: string | null
}

export interface ProfitPredictionResponse {
  predicted_profit: number
  predicted_profit_margin_pct: number
  profitability_status: string
  confidence_score: number
  influencing_factors: Record<string, any>
  is_fallback?: boolean
  warning_message?: string | null
}

export interface ExpensePredictionResponse {
  model_used: string
  category?: string | null
  predicted_expense: number
  predicted_transaction_count: number
  expense_risk_alert: string
  category_breakdown?: Record<string, number> | null
  is_fallback?: boolean
  warning_message?: string | null
}

export interface BusinessHealthResponse {
  health_score: number
  health_grade: string
  risk_rating: string
  sub_scores: Record<string, number>
  weights: Record<string, number>
  recommendations: string[]
  is_fallback?: boolean
  warning_message?: string | null
}

export interface AnomalyDetectionResponse {
  is_anomaly: boolean
  anomaly_score: number
  severity: string
  confidence: number
  reason: string
  is_fallback?: boolean
  warning_message?: string | null
}

export interface PredictionHistoryItem {
  id: string
  company_id: string
  branch_id?: string | null
  prediction_type: string
  period_start?: string | null
  period_end?: string | null
  predicted_value?: number | null
  actual_value?: number | null
  confidence_score?: number | null
  model_version?: string | null
  model_used?: string | null
  is_fallback?: boolean
  input_data: Record<string, any>
  output_data: Record<string, any>
  status: string
  created_at: string
}

