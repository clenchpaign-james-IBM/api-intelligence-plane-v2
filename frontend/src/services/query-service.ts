import { api } from './api'

export interface NewSessionRequest {
  user_id?: string
}

export interface NewSessionResponse {
  session_id: string
  created_at: string
}

export interface QueryRequest {
  query_text: string
  session_id?: string
  use_ai_agents?: boolean
}

export interface QueryResponse {
  query_id: string
  query_text: string
  response_text: string
  confidence_score: number
  results: Record<string, any>
  follow_up_queries?: string[]
  execution_time_ms: number
}

export interface FeedbackRequest {
  feedback: 'positive' | 'negative' | 'neutral'
  comment?: string
}

export interface QueryHistoryParams {
  session_id?: string
  page?: number
  page_size?: number
}

export interface QueryHistoryResponse {
  items: QueryResponse[]
  total: number
  page: number
  page_size: number
}

export const queryService = {
  /**
   * Create a new query session
   */
  createSession: async (
    request: NewSessionRequest = {}
  ): Promise<NewSessionResponse> => {
    const response = await api.post<NewSessionResponse>(
      '/api/v1/query/sessions',
      request
    )
    return response
  },

  /**
   * Execute a natural language query
   */
  executeQuery: async (request: QueryRequest): Promise<QueryResponse> => {
    const response = await api.post<QueryResponse>('/api/v1/query', request)
    return response
  },

  /**
   * Get query history
   */
  getHistory: async (
    params: QueryHistoryParams = {}
  ): Promise<QueryHistoryResponse> => {
    const response = await api.get<QueryHistoryResponse>(
      '/api/v1/query/history',
      params
    )

    return {
      items: response?.items ?? [],
      total: response?.total ?? 0,
      page: response?.page ?? 1,
      page_size: response?.page_size ?? 20,
    }
  },

  /**
   * Get a specific query by ID
   */
  getQuery: async (queryId: string): Promise<QueryResponse> => {
    const response = await api.get<QueryResponse>(`/api/v1/query/${queryId}`)
    return response
  },

  /**
   * Provide feedback on a query
   */
  provideFeedback: async (
    queryId: string,
    feedback: FeedbackRequest
  ): Promise<void> => {
    await api.post(`/api/v1/query/${queryId}/feedback`, feedback)
  },

  /**
   * Delete a query session
   */
  deleteSession: async (sessionId: string): Promise<void> => {
    await api.delete(`/api/v1/query/sessions/${sessionId}`)
  },
}

export const createQuerySession = queryService.createSession
export const executeQuery = queryService.executeQuery
export const getQueryHistory = queryService.getHistory
export const getQuery = queryService.getQuery
export const provideQueryFeedback = queryService.provideFeedback
export const deleteQuerySession = queryService.deleteSession

export default queryService

// Made with Bob