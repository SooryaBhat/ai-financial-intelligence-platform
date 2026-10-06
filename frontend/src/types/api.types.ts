// Common API response types matching the FastAPI SuccessResponse / MessageResponse schemas

export interface ApiSuccessResponse<T = unknown> {
  success: boolean
  data: T
  message?: string
}

export interface ApiMessageResponse {
  success: boolean
  message: string
}

export interface ApiErrorResponse {
  detail: string | ApiError[]
  status_code?: number
}

export interface ApiError {
  loc: (string | number)[]
  msg: string
  type: string
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
