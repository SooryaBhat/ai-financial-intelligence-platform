import api from '@/lib/api'
import { ApiSuccessResponse } from '@/types/api.types'
import { ToolCallExecution } from './erp.service'

export interface ChatSessionItem {
  id: string
  company_id: string
  user_id: string
  title: string
  summary?: string
  last_summarized_at?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ExecutionTiming {
  total_seconds?: number
  prompt_eval_seconds?: number
  eval_seconds?: number
  tools_seconds?: number
  eval_count?: number
  tok_per_sec?: number
  rounds?: number
  fast_path?: boolean
}

export interface ChatMessageItem {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  tokens_used?: number
  metadata?: {
    tools_used?: ToolCallExecution[]
    provider?: string
    model?: string
    fallback_used?: boolean
    fallback_reason?: string
    timing?: ExecutionTiming
  }
  created_at: string
}

export interface AIMemoryItem {
  id: string
  company_id: string
  user_id: string
  session_id?: string
  category: 'preference' | 'reporting' | 'business_fact' | 'goal' | 'context'
  memory_key?: string
  content: string
  confidence: number
  is_active: boolean
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface LLMProviderInfo {
  id: string
  name: string
  model: string
  badge: string
  is_default: boolean
  available: boolean
  status: 'connected' | 'configured' | 'offline' | 'model_missing' | 'missing_key' | string
  installed_models?: string[]
  base_url?: string
  description: string
}

export interface GetProvidersResponse {
  default_provider: string
  active_provider: string
  providers: LLMProviderInfo[]
}

export interface SendMessageResponse {
  message: string
  content?: string
  role: string
  session_id: string
  tools_used?: ToolCallExecution[]
  provider: string
  model: string
  status?: string
  error_details?: string
  fallback_used?: boolean
  fallback_reason?: string
  timing?: ExecutionTiming
  summary?: string
  memories_count?: number
}

export const chatService = {
  // ── LLM Providers ───────────────────────────────────────────
  async getProviders(): Promise<GetProvidersResponse> {
    const response = await api.get<ApiSuccessResponse<GetProvidersResponse>>('/api/v1/chat/providers')
    return response.data.data
  },

  // ── Sessions ────────────────────────────────────────────────
  async listSessions(search?: string, limit = 50, offset = 0): Promise<ChatSessionItem[]> {
    const params: Record<string, unknown> = { limit, offset }
    if (search && search.trim()) {
      params.search = search.trim()
    }
    const response = await api.get<ApiSuccessResponse<ChatSessionItem[]>>('/api/v1/chat/sessions', {
      params,
    })
    return response.data.data || []
  },

  async createSession(title?: string): Promise<ChatSessionItem> {
    const response = await api.post<ApiSuccessResponse<ChatSessionItem>>('/api/v1/chat/sessions', {
      title: title || 'New Conversation',
    })
    return response.data.data
  },

  async getSession(sessionId: string): Promise<ChatSessionItem> {
    const response = await api.get<ApiSuccessResponse<ChatSessionItem>>(`/api/v1/chat/sessions/${sessionId}`)
    return response.data.data
  },

  async updateSession(sessionId: string, data: { title?: string }): Promise<ChatSessionItem> {
    const response = await api.patch<ApiSuccessResponse<ChatSessionItem>>(
      `/api/v1/chat/sessions/${sessionId}`,
      data
    )
    return response.data.data
  },

  async deleteSession(sessionId: string): Promise<void> {
    await api.delete(`/api/v1/chat/sessions/${sessionId}`)
  },

  // ── Messages ────────────────────────────────────────────────
  async listMessages(sessionId: string, limit = 100, offset = 0): Promise<ChatMessageItem[]> {
    const response = await api.get<ApiSuccessResponse<ChatMessageItem[]>>(
      `/api/v1/chat/sessions/${sessionId}/messages`,
      { params: { limit, offset } }
    )
    return response.data.data || []
  },

  async sendMessage(
    message: string,
    sessionId?: string,
    provider?: string
  ): Promise<SendMessageResponse> {
    const url = sessionId ? `/api/v1/chat/sessions/${sessionId}/messages` : '/api/v1/chat'
    const payload: Record<string, unknown> = {
      message,
      content: message,
    }
    if (sessionId) payload.session_id = sessionId
    if (provider) payload.provider = provider

    const startTime = performance.now()
    console.log(`[ChatService] Sending message to provider='${provider || 'default'}' (session: ${sessionId || 'new'})...`)
    try {
      const response = await api.post<ApiSuccessResponse<SendMessageResponse>>(url, payload, {
        timeout: 300000, // 300s (5 min) aligned with backend timeout
      })
      const elapsed = ((performance.now() - startTime) / 1000).toFixed(2)
      console.log(`[ChatService] Response received in ${elapsed}s:`, response.data.data)
      return response.data.data
    } catch (err: unknown) {
      const elapsed = ((performance.now() - startTime) / 1000).toFixed(2)
      console.error(`[ChatService] Message failed after ${elapsed}s:`, err)
      throw err
    }
  },

  // ── AI Memories ─────────────────────────────────────────────
  async listMemories(category?: string, search?: string): Promise<AIMemoryItem[]> {
    const params: Record<string, unknown> = {}
    if (category) params.category = category
    if (search && search.trim()) params.search = search.trim()

    const response = await api.get<ApiSuccessResponse<AIMemoryItem[]>>('/api/v1/chat/memories', {
      params,
    })
    return response.data.data || []
  },

  async createMemory(payload: {
    content: string
    category?: string
    memory_key?: string
    session_id?: string
  }): Promise<AIMemoryItem> {
    const response = await api.post<ApiSuccessResponse<AIMemoryItem>>('/api/v1/chat/memories', {
      content: payload.content,
      category: payload.category || 'preference',
      memory_key: payload.memory_key,
      session_id: payload.session_id,
    })
    return response.data.data
  },

  async updateMemory(
    memoryId: string,
    payload: {
      content?: string
      category?: string
      is_active?: boolean
    }
  ): Promise<AIMemoryItem> {
    const response = await api.patch<ApiSuccessResponse<AIMemoryItem>>(
      `/api/v1/chat/memories/${memoryId}`,
      payload
    )
    return response.data.data
  },

  async deleteMemory(memoryId: string): Promise<void> {
    await api.delete(`/api/v1/chat/memories/${memoryId}`)
  },

  async clearAllMemories(): Promise<void> {
    await api.delete('/api/v1/chat/memories')
  },
}
