/**
 * API Client Service
 * 
 * Provides a centralized HTTP client for all backend API calls.
 * Features:
 * - Base URL configuration from environment
 * - Request/response interceptors
 * - Error handling and transformation
 * - Type-safe API methods
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

// API Response types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

// API Client Configuration
// Use relative path in production/Docker (goes through Vite proxy)
// Use full URL in development when running frontend standalone
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const API_TIMEOUT = 30000; // 30 seconds

/**
 * Create and configure Axios instance
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // Add authentication token if available
      const token = localStorage.getItem('auth_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // Log request in development
      if (import.meta.env.DEV) {
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
          params: config.params,
          data: config.data,
        });
      }

      return config;
    },
    (error: AxiosError) => {
      console.error('[API Request Error]', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      // Log response in development
      if (import.meta.env.DEV) {
        console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
          status: response.status,
          data: response.data,
        });
      }

      return response;
    },
    (error: AxiosError) => {
      // Transform error for consistent handling
      const apiError: ApiError = {
        message: error.message || 'An unexpected error occurred',
        status: error.response?.status || 500,
        details: error.response?.data,
      };

      // Handle specific error cases
      if (error.response?.status === 401) {
        // Unauthorized - clear token and redirect to login
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      } else if (error.response?.status === 403) {
        apiError.message = 'Access forbidden';
      } else if (error.response?.status === 404) {
        apiError.message = 'Resource not found';
      } else if (error.response?.status === 500) {
        apiError.message = 'Internal server error';
      }

      console.error('[API Response Error]', apiError);
      return Promise.reject(apiError);
    }
  );

  return client;
};

// Create singleton instance
const apiClient = createApiClient();

/**
 * API Service Methods
 */
export const api = {
  // Generic HTTP methods
  get: <T = any>(url: string, params?: any): Promise<T> =>
    apiClient.get(url, { params }).then((res) => res.data),

  post: <T = any>(url: string, data?: any): Promise<T> =>
    apiClient.post(url, data).then((res) => res.data),

  put: <T = any>(url: string, data?: any): Promise<T> =>
    apiClient.put(url, data).then((res) => res.data),

  patch: <T = any>(url: string, data?: any): Promise<T> =>
    apiClient.patch(url, data).then((res) => res.data),

  delete: <T = any>(url: string): Promise<T> =>
    apiClient.delete(url).then((res) => res.data),

  // Health check
  health: () => api.get('/health'),

  // Gateway endpoints
  gateways: {
    list: () => api.get('/api/v1/gateways'),
    get: (id: string) => api.get(`/api/v1/gateways/${id}`),
    create: (data: any) => api.post('/api/v1/gateways', data),
    update: (id: string, data: any) => api.put(`/api/v1/gateways/${id}`, data),
    delete: (id: string) => api.delete(`/api/v1/gateways/${id}`),
    sync: (id: string) => api.post(`/api/v1/gateways/${id}/sync`),
  },

  // API endpoints
  apis: {
    list: (params?: any) => api.get('/api/v1/apis', params),
    get: (id: string) => api.get(`/api/v1/apis/${id}`),
    search: (query: string) => api.get('/api/v1/apis/search', { query }),
  },

  // Metrics endpoints
  metrics: {
    list: (params?: any) => api.get('/api/v1/metrics', params),
    get: (id: string) => api.get(`/api/v1/metrics/${id}`),
    aggregate: (params: any) => api.post('/api/v1/metrics/aggregate', params),
  },

  // Predictions endpoints
  predictions: {
    list: (params?: any) => api.get('/api/v1/predictions', params),
    get: (id: string) => api.get(`/api/v1/predictions/${id}`),
    create: (data: any) => api.post('/api/v1/predictions', data),
    generate: (params?: any) => {
      // Convert params object to query string
      const queryParams = new URLSearchParams();
      if (params?.api_id) queryParams.append('api_id', params.api_id);
      if (params?.min_confidence !== undefined) queryParams.append('min_confidence', params.min_confidence.toString());
      if (params?.use_ai !== undefined) queryParams.append('use_ai', params.use_ai.toString());
      
      const queryString = queryParams.toString();
      return api.post(`/api/v1/predictions/generate${queryString ? `?${queryString}` : ''}`);
    },
    // AI-enhanced endpoints
    generateAiEnhanced: (apiId: string, minConfidence?: number) => {
      const queryParams = new URLSearchParams();
      queryParams.append('api_id', apiId);
      if (minConfidence !== undefined) queryParams.append('min_confidence', minConfidence.toString());
      return api.post(`/api/v1/predictions/ai-enhanced?${queryParams.toString()}`);
    },
    getExplanation: (id: string) => api.get(`/api/v1/predictions/${id}/explanation`),
  },

  // Security endpoints
  security: {
    vulnerabilities: {
      list: (params?: any) => api.get('/api/v1/security/vulnerabilities', params),
      get: (id: string) => api.get(`/api/v1/security/vulnerabilities/${id}`),
      scan: (apiId: string) => api.post(`/api/v1/security/scan/${apiId}`),
    },
  },

  // Optimization recommendations endpoints
  recommendations: {
    list: (params?: any) => api.get('/api/v1/recommendations', params),
    get: (id: string) => api.get(`/api/v1/recommendations/${id}`),
    generate: (apiId: string, minImpact?: number, useAi?: boolean) => {
      const params: any = { api_id: apiId };
      if (minImpact !== undefined) params.min_impact = minImpact;
      if (useAi !== undefined) params.use_ai = useAi;
      return api.post('/api/v1/recommendations/generate', params);
    },
    stats: (params?: any) => api.get('/api/v1/recommendations/stats', params),
    // AI-enhanced endpoints
    generateAiEnhanced: (apiId: string, minImpact?: number) => {
      const params: any = { api_id: apiId };
      if (minImpact !== undefined) params.min_impact = minImpact;
      return api.post('/api/v1/optimization/ai-enhanced', params);
    },
    getInsights: (id: string) => api.get(`/api/v1/optimization/${id}/insights`),
  },

  // Rate limit endpoints
  rateLimits: {
    list: (params?: any) => api.get('/api/v1/rate-limits', params),
    get: (id: string) => api.get(`/api/v1/rate-limits/${id}`),
    create: (data: any) => api.post('/api/v1/rate-limits', data),
    activate: (id: string) => api.post(`/api/v1/rate-limits/${id}/activate`),
    deactivate: (id: string) => api.post(`/api/v1/rate-limits/${id}/deactivate`),
    suggest: (apiId: string) => api.get(`/api/v1/rate-limits/suggest/${apiId}`),
    effectiveness: (id: string) => api.get(`/api/v1/rate-limits/${id}/effectiveness`),
  },

  // Query endpoints
  query: {
    execute: (query: string) => api.post('/api/v1/query', { query }),
    history: (params?: any) => api.get('/api/v1/query/history', params),
  },
};

export default api;

// Made with Bob
