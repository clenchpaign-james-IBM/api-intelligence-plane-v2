import type {
  Metric,
  MetricsResponse,
  MetricsTimeSeriesResponse,
  TimeBucket
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const metricsService = {
  /**
   * Get time-bucketed metrics for a specific API
   * This is the new primary method for fetching metrics with time buckets
   */
  async getMetrics(
    apiId: string,
    params?: {
      start_time?: string; // ISO 8601 timestamp
      end_time?: string; // ISO 8601 timestamp
      time_bucket?: TimeBucket; // '1m', '5m', '1h', '1d'
    }
  ): Promise<MetricsResponse> {
    const queryParams = new URLSearchParams();
    if (params?.start_time) queryParams.append('start_time', params.start_time);
    if (params?.end_time) queryParams.append('end_time', params.end_time);
    if (params?.time_bucket) queryParams.append('time_bucket', params.time_bucket);

    const url = `${API_BASE_URL}/api/v1/apis/${apiId}/metrics${queryParams.toString() ? `?${queryParams}` : ''}`;
    const response = await fetch(url);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`API not found: ${apiId}`);
      }
      throw new Error(`Failed to fetch metrics: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get optimal time bucket based on time range
   * Helper function to automatically select appropriate granularity
   */
  getOptimalTimeBucket(startTime: Date, endTime: Date): TimeBucket {
    const durationMs = endTime.getTime() - startTime.getTime();
    const durationHours = durationMs / (1000 * 60 * 60);

    if (durationHours <= 1) return '1m';      // Last hour: 1-minute buckets
    if (durationHours <= 6) return '5m';      // Last 6 hours: 5-minute buckets
    if (durationHours <= 48) return '1h';     // Last 2 days: 1-hour buckets
    return '1d';                               // More than 2 days: 1-day buckets
  },

  /**
   * Get the most recent metric snapshot for a specific API using time-bucketed data.
   */
  async getCurrent(apiId: string, time_bucket: TimeBucket = '5m'): Promise<Metric | null> {
    const response = await this.getMetrics(apiId, { time_bucket });

    if (!response.time_series || response.time_series.length === 0) {
      return null;
    }

    const latestPoint = response.time_series[response.time_series.length - 1];
    const status2xx = response.status_breakdown?.['2xx'] ?? 0;
    const status3xx = response.status_breakdown?.['3xx'] ?? 0;
    const status4xx = response.status_breakdown?.['4xx'] ?? 0;
    const status5xx = response.status_breakdown?.['5xx'] ?? 0;

    return {
      id: `${apiId}-${latestPoint.timestamp}-${time_bucket}`,
      api_id: apiId,
      gateway_id: '',
      timestamp: latestPoint.timestamp,
      time_bucket,
      request_count: latestPoint.request_count ?? 0,
      success_count: latestPoint.success_count ?? 0,
      failure_count: latestPoint.failure_count ?? 0,
      response_time_avg: latestPoint.response_time_avg ?? response.aggregated.avg_response_time ?? 0,
      response_time_p50: latestPoint.response_time_p50 ?? 0,
      response_time_p95: latestPoint.response_time_p95 ?? response.aggregated.p95_response_time ?? 0,
      response_time_p99: latestPoint.response_time_p99 ?? response.aggregated.p99_response_time ?? 0,
      response_time_min: latestPoint.response_time_avg ?? response.aggregated.avg_response_time ?? 0,
      response_time_max: latestPoint.response_time_p99 ?? response.aggregated.p99_response_time ?? 0,
      gateway_time_avg: latestPoint.gateway_time_avg ?? response.timing_breakdown.avg_gateway_time ?? 0,
      backend_time_avg: latestPoint.backend_time_avg ?? response.timing_breakdown.avg_backend_time ?? 0,
      cache_hit_rate: latestPoint.cache_hit_rate ?? response.cache_metrics.avg_hit_rate ?? 0,
      cache_hit_count: response.cache_metrics.total_hits ?? 0,
      cache_miss_count: response.cache_metrics.total_misses ?? 0,
      cache_bypass_count: response.cache_metrics.total_bypasses ?? 0,
      total_data_size: 0,
      avg_request_size: 0,
      avg_response_size: 0,
      status_2xx_count: status2xx,
      status_3xx_count: status3xx,
      status_4xx_count: status4xx,
      status_5xx_count: status5xx,
      timeout_count: 0,
      throughput: latestPoint.request_count ?? 0,
      status_codes: {
        '2xx': status2xx,
        '3xx': status3xx,
        '4xx': status4xx,
        '5xx': status5xx,
      },
    };
  },

  /**
   * Get time-series metrics for a specific API using vendor-neutral time bucket selection.
   */
  async getTimeSeries(
    apiId: string,
    params?: {
      start?: string;
      end?: string;
      interval?: number;
      time_bucket?: TimeBucket;
    }
  ): Promise<MetricsTimeSeriesResponse> {
    let derivedBucket: TimeBucket = params?.time_bucket ?? '5m';

    if (!params?.time_bucket && params?.start && params?.end) {
      derivedBucket = this.getOptimalTimeBucket(new Date(params.start), new Date(params.end));
    }

    const response = await this.getMetrics(apiId, {
      start_time: params?.start,
      end_time: params?.end,
      time_bucket: derivedBucket,
    });

    return {
      api_id: response.api_id,
      start: params?.start ?? '',
      end: params?.end ?? '',
      interval_minutes: params?.interval ?? 0,
      data_points: response.total_data_points,
      metrics: response.time_series,
    };
  },

  /**
   * Get aggregated metrics for a specific API over a time range
   */
  async getAggregated(
    apiId: string,
    params: {
      start: string; // ISO 8601 timestamp
      end: string; // ISO 8601 timestamp
      aggregation?: 'avg' | 'min' | 'max' | 'sum';
    }
  ): Promise<Metric> {
    const queryParams = new URLSearchParams();
    queryParams.append('start', params.start);
    queryParams.append('end', params.end);
    if (params.aggregation) queryParams.append('aggregation', params.aggregation);

    const url = `${API_BASE_URL}/api/v1/apis/${apiId}/metrics/aggregated?${queryParams}`;
    const response = await fetch(url);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`API not found: ${apiId}`);
      }
      throw new Error(`Failed to fetch aggregated metrics: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Trigger metrics collection for a specific API
   */
  async collect(apiId: string): Promise<{ message: string; metrics: Metric }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/apis/${apiId}/metrics/collect`, {
      method: 'POST',
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`API not found: ${apiId}`);
      }
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to collect metrics: ${error.detail || response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get health score for a specific API
   */
  async getHealthScore(apiId: string): Promise<{ api_id: string; health_score: number; timestamp: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/apis/${apiId}/metrics/health`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`API not found: ${apiId}`);
      }
      throw new Error(`Failed to fetch health score: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get metrics summary across all APIs
   */
  async getSummary(params?: {
    gateway_id?: string;
    status?: string;
  }): Promise<{
    total_apis: number;
    avg_response_time: number;
    avg_error_rate: number;
    avg_throughput: number;
    avg_availability: number;
    avg_health_score: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params?.gateway_id) queryParams.append('gateway_id', params.gateway_id);
    if (params?.status) queryParams.append('status', params.status);

    const url = `${API_BASE_URL}/api/v1/metrics/summary${queryParams.toString() ? `?${queryParams}` : ''}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch metrics summary: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Compare metrics between two APIs
   */
  async compare(
    apiId1: string,
    apiId2: string,
    params?: {
      start?: string;
      end?: string;
    }
  ): Promise<{
    api1: Metric;
    api2: Metric;
    comparison: {
      response_time_diff: number;
      error_rate_diff: number;
      throughput_diff: number;
      availability_diff: number;
    };
  }> {
    const queryParams = new URLSearchParams();
    queryParams.append('api_id_1', apiId1);
    queryParams.append('api_id_2', apiId2);
    if (params?.start) queryParams.append('start', params.start);
    if (params?.end) queryParams.append('end', params.end);

    const url = `${API_BASE_URL}/api/v1/metrics/compare?${queryParams}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to compare metrics: ${response.statusText}`);
    }

    return response.json();
  },
};

// Made with Bob
