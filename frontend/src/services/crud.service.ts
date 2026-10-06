import api from '@/lib/api'
import { ApiSuccessResponse, ApiMessageResponse, PaginatedResult } from '@/types/api.types'

export function createCrudService<T = any, CreateDTO = any, UpdateDTO = any>(endpoint: string) {
  return {
    async list(params?: { page?: number; page_size?: number; search?: string; [key: string]: unknown }): Promise<PaginatedResult<T>> {
      const response = await api.get<ApiSuccessResponse<PaginatedResult<T> | T[]>>(endpoint, { params })
      const data = response.data.data
      if (Array.isArray(data)) {
        return {
          items: data as T[],
          total: data.length,
          page: params?.page || 1,
          page_size: params?.page_size || data.length || 20,
          total_pages: 1,
        }
      }
      return (data as PaginatedResult<T>) || { items: [], total: 0, page: 1, page_size: 20, total_pages: 1 }
    },

    async getById(id: string): Promise<T> {
      const response = await api.get<ApiSuccessResponse<T>>(`${endpoint}/${id}`)
      return response.data.data
    },

    async create(payload: CreateDTO): Promise<T> {
      const response = await api.post<ApiSuccessResponse<T>>(endpoint, payload)
      return response.data.data
    },

    async update(id: string, payload: UpdateDTO): Promise<T> {
      const response = await api.patch<ApiSuccessResponse<T>>(`${endpoint}/${id}`, payload)
      return response.data.data
    },

    async delete(id: string): Promise<ApiMessageResponse> {
      const response = await api.delete<ApiMessageResponse>(`${endpoint}/${id}`)
      return response.data
    },
  }
}
