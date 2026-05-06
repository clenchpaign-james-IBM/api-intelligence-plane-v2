/**
 * Prediction Service Client
 *
 * Provides API methods for prediction-related operations.
 * Extends the base API client with prediction-specific functionality.
 */

import { api } from './api';
import type {
  Prediction,
  PredictionSeverity,
  PredictionStatus,
  PredictionRemediationPlan,
  PredictionRemediationAction
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

// Remediation Request/Response Types
export interface RemediationPlanResponse {
  prediction_id: string;
  plan: PredictionRemediationPlan;
  requires_approval: boolean;
  estimated_time_minutes: number;
}

export interface RemediationRequest {
  remediation_strategy?: 'conservative' | 'balanced' | 'aggressive';
  auto_approve?: boolean;
  override_config?: Record<string, any>;
}

export interface RemediationExecutionResponse {
  prediction_id: string;
  status: string;
  actions: PredictionRemediationAction[];
  message: string;
}

export interface VerificationResponse {
  prediction_id: string;
  verified: boolean;
  effectiveness_score: number;
  verification_method: string;
  verification_time: string;
  details: Record<string, any>;
}

export interface RollbackResponse {
  prediction_id: string;
  status: string;
  rolled_back_actions: string[];
  message: string;
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

  /**
   * Generate remediation plan for a prediction
   *
   * @param gatewayId - Gateway ID
   * @param predictionId - Prediction ID
   * @param forceRegenerate - Force regeneration of plan
   * @returns Promise resolving to remediation plan
   */
  generateRemediationPlan: async (
    gatewayId: string,
    predictionId: string,
    forceRegenerate: boolean = false
  ): Promise<RemediationPlanResponse> => {
    const url = `${API_BASE_URL}/api/v1/gateways/${gatewayId}/predictions/${predictionId}/remediation-plan?force_regenerate=${forceRegenerate}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to generate remediation plan: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Execute remediation for a prediction
   *
   * @param gatewayId - Gateway ID
   * @param predictionId - Prediction ID
   * @param request - Remediation request parameters
   * @returns Promise resolving to execution response
   */
  remediate: async (
    gatewayId: string,
    predictionId: string,
    request: RemediationRequest = {}
  ): Promise<RemediationExecutionResponse> => {
    const url = `${API_BASE_URL}/api/v1/gateways/${gatewayId}/predictions/${predictionId}/remediate`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to remediate prediction: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Verify remediation effectiveness
   *
   * @param gatewayId - Gateway ID
   * @param predictionId - Prediction ID
   * @param verificationMethod - Verification method (automated or manual)
   * @returns Promise resolving to verification response
   */
  verifyRemediation: async (
    gatewayId: string,
    predictionId: string,
    verificationMethod: 'automated' | 'manual' = 'automated'
  ): Promise<VerificationResponse> => {
    const url = `${API_BASE_URL}/api/v1/gateways/${gatewayId}/predictions/${predictionId}/verify-remediation?verification_method=${verificationMethod}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to verify remediation: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Rollback remediation actions
   *
   * @param gatewayId - Gateway ID
   * @param predictionId - Prediction ID
   * @param actionId - Optional specific action ID to rollback
   * @returns Promise resolving to rollback response
   */
  rollback: async (
    gatewayId: string,
    predictionId: string,
    actionId?: string
  ): Promise<RollbackResponse> => {
    const url = `${API_BASE_URL}/api/v1/gateways/${gatewayId}/predictions/${predictionId}/rollback${actionId ? `?action_id=${actionId}` : ''}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to rollback remediation: ${response.statusText}`);
    }

    return response.json();
  },
};

export default predictionService;

// Made with Bob
