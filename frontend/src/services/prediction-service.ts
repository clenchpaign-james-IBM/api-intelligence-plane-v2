/**
 * Prediction Service Client
 * 
 * Provides API methods for prediction-related operations.
 * Extends the base API client with prediction-specific functionality.
 */

import { api } from './api';
import type { Prediction, PredictionSeverity, PredictionStatus } from '../types';

export interface PredictionListParams {
  severity?: PredictionSeverity;
  status?: PredictionStatus;
  gateway_id?: string;
  api_id?: string;
  limit?: number;
  offset?: number;
}

export interface PredictionListResponse {
  predictions: Prediction[];
  total: number;
  limit: number;
  offset: number;
}

export interface PredictionExplanationResponse {
  prediction_id: string;
  ai_explanation: string;
  ai_enhanced: boolean;
  recommended_actions: string[];
  contributing_factors: Array<{
    factor: string;
    current_value: number;
    threshold: number;
    trend: string;
    weight: number;
  }>;
}

/**
 * Prediction Service
 * 
 * Handles all prediction-related API calls including:
 * - Listing predictions with filters
 * - Getting prediction details
 * - Fetching AI-enhanced explanations
 * - Creating manual predictions
 */
export const predictionService = {
  /**
   * List predictions with optional filters
   * 
   * @param params - Filter parameters (severity, status, gateway_id, api_id, pagination)
   * @returns Promise resolving to paginated prediction list
   */
  list: (params?: PredictionListParams): Promise<PredictionListResponse> => {
    return api.predictions.list(params);
  },

  /**
   * Get a single prediction by ID
   * 
   * @param id - Prediction ID
   * @returns Promise resolving to prediction details
   */
  get: (id: string): Promise<Prediction> => {
    return api.predictions.get(id);
  },

  /**
   * Get AI-enhanced explanation for a prediction
   * 
   * @param id - Prediction ID
   * @returns Promise resolving to AI explanation and details
   */
  getExplanation: (id: string): Promise<PredictionExplanationResponse> => {
    return api.predictions.getExplanation(id);
  },

  /**
   * Create a manual prediction
   * 
   * @param data - Prediction data
   * @returns Promise resolving to created prediction
   */
  create: (data: Partial<Prediction>): Promise<Prediction> => {
    return api.predictions.create(data);
  },

  /**
   * Get predictions for a specific API
   * 
   * @param apiId - API ID
   * @param params - Additional filter parameters
   * @returns Promise resolving to prediction list
   */
  getByApi: (apiId: string, params?: Omit<PredictionListParams, 'api_id'>): Promise<PredictionListResponse> => {
    return api.predictions.list({ ...params, api_id: apiId });
  },

  /**
   * Get predictions for a specific gateway
   * 
   * @param gatewayId - Gateway ID
   * @param params - Additional filter parameters
   * @returns Promise resolving to prediction list
   */
  getByGateway: (gatewayId: string, params?: Omit<PredictionListParams, 'gateway_id'>): Promise<PredictionListResponse> => {
    return api.predictions.list({ ...params, gateway_id: gatewayId });
  },

  /**
   * Get active predictions (status = 'active')
   * 
   * @param params - Additional filter parameters
   * @returns Promise resolving to active predictions
   */
  getActive: (params?: Omit<PredictionListParams, 'status'>): Promise<PredictionListResponse> => {
    return api.predictions.list({ ...params, status: 'active' });
  },

  /**
   * Get critical predictions (severity = 'critical')
   * 
   * @param params - Additional filter parameters
   * @returns Promise resolving to critical predictions
   */
  getCritical: (params?: Omit<PredictionListParams, 'severity'>): Promise<PredictionListResponse> => {
    return api.predictions.list({ ...params, severity: 'critical' });
  },
};

export default predictionService;

// Made with Bob
