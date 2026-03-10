import type { Metric, MetricsTimeSeriesResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const metricsService = {
  /**
   * Get current metrics for a specific API
   */
  async getCurrent(apiId: string): Promise<Metric> {
    const response = await fetch(`${API_BASE_URL}/api/v1/apis/${apiId}/metrics/current`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`API not found: ${apiId}`);
      }
      throw new Error(`Failed to fetch current metrics: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get time-series metrics for a specific API
   */
  async getTimeSeries(
    apiId: string,
    params?: {
      start?: string; // ISO 8601 timestamp
      end?: string; // ISO 8601 timestamp
      interval?: number; // minutes
    }
  ): Promise<MetricsTimeSeriesResponse> {
    const queryParams = new URLSearchParams();
    if (params?.start) queryParams.append('start', params.start);
    if (params?.end) queryParams.append('end', params.end);
    if (params?.interval !== undefined) queryParams.append('interval', params.interval.toString());

    const url = `${API_BASE_URL}/api/v1/apis/${apiId}/metrics${queryParams.toString() ? `?${queryParams}` : ''}`;
    const response = await fetch(url);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`API not found: ${apiId}`);
      }
      throw new Error(`Failed to fetch metrics time series: ${response.statusText}`);
    }

    return response.json();
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
