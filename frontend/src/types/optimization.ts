export interface AIContext {
  performance_analysis?: string;
  implementation_guidance?: string;
  prioritization?: string;
  generated_at?: string;
}

export interface EstimatedImpact {
  metric: string;
  current_value: number;
  expected_value: number;
  improvement_percentage: number;
  confidence: number;
}

export interface ActualImpact {
  metric: string;
  before_value: number;
  after_value: number;
  actual_improvement: number;
}

export interface ValidationResults {
  success: boolean;
  expected_improvement: number;
  actual_improvement: number;
  improvement_percentage: number;
  validation_timestamp: string;
  metrics_analyzed: Record<string, ActualImpact>;
  confidence_score: number;
  message: string;
}

export type OptimizationActionType = 'apply_policy' | 'remove_policy' | 'validate' | 'manual_configuration';
export type OptimizationActionStatus = 'completed' | 'pending' | 'failed' | 'in_progress';

export interface OptimizationAction {
  action: string;
  type: OptimizationActionType;
  status: OptimizationActionStatus;
  performed_at: string;
  performed_by: string;
  gateway_policy_id?: string;
  error_message?: string;
  metadata?: Record<string, any>;
}

export interface OptimizationRecommendation {
  id: string;
  gateway_id: string;
  api_id: string;
  api_name?: string;
  recommendation_type: string;
  title: string;
  description: string;
  priority: string;
  estimated_impact: EstimatedImpact;
  implementation_effort: string;
  implementation_steps: string[];
  status: string;
  implemented_at?: string;
  validation_results?: ValidationResults;
  remediation_actions?: OptimizationAction[];
  cost_savings?: number;
  metadata?: Record<string, any>;
  vendor_metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  expires_at?: string;
  ai_context?: AIContext;
}

export interface ValidationResponse {
  recommendation_id: string;
  metric: string;
  expected_improvement: number;
  actual_improvement: number;
  success: boolean;
  validated_at: string;
  before_value: number;
  after_value: number;
  samples_analyzed: number;
  validation_window_hours: number;
}

export interface ApplyRecommendationResponse {
  success: boolean;
  requires_manual_configuration?: boolean;
  requires_manual_action?: boolean;
  recommendation_id: string;
  api_id: string;
  gateway_id: string;
  policy_type: string;
  message: string;
  applied_at?: string;
  instructions?: string[];
  policy_id?: string;
  status?: string;
}

// Made with Bob
