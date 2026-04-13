import { api } from './api'
import type { Metric, TimeBucket, TransactionalLog } from '../types'

export interface AnalyticsFilters {
  gateway_id?: string
  api_id?: string
  application_id?: string
  start_time?: string
  end_time?: string
  time_bucket?: TimeBucket
  limit?: number
  offset?: number
}

export interface MetricsQueryParams extends AnalyticsFilters {
  time_bucket?: TimeBucket
}

export interface TransactionalLogsQueryParams extends AnalyticsFilters {}

export interface AnalyticsMetricsResponse {
  items: Metric[]
  total: number
  time_bucket: TimeBucket
}

export interface AnalyticsLogsResponse {
  items: TransactionalLog[]
  total: number
}

export const analyticsService = {
  getMetrics: async (
    params: MetricsQueryParams = {}
  ): Promise<AnalyticsMetricsResponse> => {
    const response = await api.get<AnalyticsMetricsResponse>(
      '/api/v1/analytics/metrics',
      params
    )

    return {
      items: response?.items ?? [],
      total: response?.total ?? 0,
      time_bucket: response?.time_bucket ?? params.time_bucket ?? '1h',
    }
  },

  getLogsForMetric: async (
    metricId: string,
    params: AnalyticsFilters = {}
  ): Promise<AnalyticsLogsResponse> => {
    const response = await api.get<AnalyticsLogsResponse>(
      `/api/v1/analytics/metrics/${metricId}/logs`,
      params
    )

    return {
      items: response?.items ?? [],
      total: response?.total ?? 0,
    }
  },

  getTransactionalLogs: async (
    params: TransactionalLogsQueryParams = {}
  ): Promise<AnalyticsLogsResponse> => {
    const response = await api.get<AnalyticsLogsResponse>(
      '/api/v1/analytics/logs',
      params
    )

    return {
      items: response?.items ?? [],
      total: response?.total ?? 0,
    }
  },
}

export const getAnalyticsMetrics = analyticsService.getMetrics
export const getLogsForMetric = analyticsService.getLogsForMetric
export const getTransactionalLogs = analyticsService.getTransactionalLogs

export default analyticsService

// Made with Bob
