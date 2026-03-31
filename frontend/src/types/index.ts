/**
 * TypeScript type definitions for API Intelligence Plane frontend.
 * 
 * These types match the backend data models and API responses.
 */

// API Entity
export interface API {
  id: string;
  gateway_id: string;
  name: string;
  version?: string;
  base_path: string;
  endpoints: Endpoint[];
  methods: string[];
  authentication_type: AuthenticationType;
  authentication_config?: Record<string, any>;
  ownership?: Ownership;
  tags?: string[];
  is_shadow: boolean;
  discovery_method: DiscoveryMethod;
  discovered_at: string;
  last_seen_at: string;
  status: APIStatus;
  health_score: number;
  current_metrics: CurrentMetrics;
  security_policies?: SecurityPolicies;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SecurityPolicies {
  authentication_required: boolean;
  authorization_enabled: boolean;
  rate_limiting_enabled: boolean;
  rate_limit_config?: {
    requests_per_minute: number;
    burst_size: number;
  };
  tls_enforced: boolean;
  tls_version?: string;
  cors_enabled: boolean;
  cors_config?: {
    allowed_origins: string[];
    allowed_methods: string[];
    allow_credentials: boolean;
  };
  input_validation_enabled: boolean;
  output_sanitization_enabled: boolean;
  logging_enabled: boolean;
  encryption_at_rest: boolean;
  waf_enabled: boolean;
  ip_whitelisting_enabled: boolean;
  allowed_ips?: string[];
  api_key_rotation_enabled: boolean;
  key_rotation_days?: number;
  compliance_standards?: string[];
  last_policy_update?: string;
}

export interface Endpoint {
  path: string;
  method: string;
  description?: string;
  parameters?: Parameter[];
  response_codes?: number[];
}

export interface Parameter {
  name: string;
  type: 'path' | 'query' | 'header' | 'body';
  data_type: string;
  required: boolean;
}

export interface Ownership {
  team?: string;
  contact?: string;
  repository?: string;
}

export interface CurrentMetrics {
  response_time_p50: number;
  response_time_p95: number;
  response_time_p99: number;
  error_rate: number;
  throughput: number;
  availability: number;
  last_error?: string;
  measured_at: string;
}

export type AuthenticationType = 'none' | 'basic' | 'bearer' | 'oauth2' | 'api_key' | 'custom';
export type DiscoveryMethod = 'registered' | 'traffic_analysis' | 'log_analysis';
export type APIStatus = 'active' | 'inactive' | 'deprecated' | 'failed';

// Gateway Entity
export interface Gateway {
  id: string;
  name: string;
  vendor: GatewayVendor;
  version?: string;
  connection_url: string;
  connection_type: ConnectionType;
  credentials: GatewayCredentials;
  capabilities: string[];
  status: GatewayStatus;
  last_connected_at?: string;
  last_error?: string;
  api_count: number;
  metrics_enabled: boolean;
  security_scanning_enabled: boolean;
  rate_limiting_enabled: boolean;
  configuration?: Record<string, any>;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface GatewayCredentials {
  type: string;
  api_key?: string;
  username?: string;
  password?: string;
  token?: string;
  [key: string]: any;
}

export type GatewayVendor = 'native' | 'kong' | 'apigee' | 'aws' | 'azure' | 'custom';

// Query Entity
export interface Query {
  id: string;
  session_id: string;
  user_id?: string;
  query_text: string;
  query_type: NLQueryType;
  interpreted_intent: InterpretedIntent;
  opensearch_query?: Record<string, any>;
  results: QueryResults;
  response_text: string;
  confidence_score: number;
  execution_time_ms: number;
  feedback?: UserFeedback;
  feedback_comment?: string;
  follow_up_queries?: string[];
  metadata?: Record<string, any>;
  created_at: string;
}

export interface InterpretedIntent {
  action: string;
  entities: string[];
  filters: Record<string, any>;
  time_range?: TimeRange;
}

export interface TimeRange {
  start: string;
  end: string;
}

export interface QueryResults {
  data: any[];
  count: number;
  execution_time: number;
  aggregations?: Record<string, any>;
}

export type NLQueryType = 'status' | 'trend' | 'prediction' | 'security' | 'performance' | 'comparison' | 'general';
export type UserFeedback = 'helpful' | 'not_helpful' | 'partially_helpful';

// Query Request/Response
export interface QueryRequest {
  query_text: string;
  session_id?: string;
}

export interface QueryResponse {
  query_id: string;
  query_text: string;
  response_text: string;
  confidence_score: number;
  results: Record<string, any>;
  follow_up_queries?: string[];
  execution_time_ms: number;
}

export interface FeedbackRequest {
  feedback: UserFeedback;
  comment?: string;
}
export type ConnectionType = 'rest_api' | 'grpc' | 'graphql';
export type GatewayStatus = 'connected' | 'disconnected' | 'error' | 'maintenance';

// Metric Entity
export interface Metric {
  id: string;
  api_id: string;
  gateway_id: string;
  timestamp: string;
  response_time_p50: number;
  response_time_p95: number;
  response_time_p99: number;
  error_rate: number;
  error_count: number;
  request_count: number;
  throughput: number;
  availability: number;
  status_codes: Record<string, number>;
  endpoint_metrics?: EndpointMetric[];
  metadata?: Record<string, any>;
}

export interface EndpointMetric {
  endpoint: string;
  method: string;
  response_time_p50: number;
  response_time_p95: number;
  response_time_p99: number;
  error_rate: number;
  request_count: number;
}

// Prediction Entity
export interface Prediction {
  id: string;
  api_id: string;
  api_name?: string;
  prediction_type: PredictionType;
  predicted_at: string;
  predicted_time: string;
  confidence_score: number;
  severity: PredictionSeverity;
  status: PredictionStatus;
  description?: string;
  contributing_factors: ContributingFactor[];
  recommended_actions: string[];
  actual_outcome?: ActualOutcome;
  actual_time?: string;
  accuracy_score?: number;
  model_version: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ContributingFactor {
  factor: string;
  current_value: number;
  threshold: number;
  trend: string;
  weight: number;
}

export type PredictionType = 'failure' | 'degradation' | 'capacity' | 'security';
export type PredictionSeverity = 'critical' | 'high' | 'medium' | 'low';
export type PredictionStatus = 'active' | 'resolved' | 'false_positive' | 'expired';
export type ActualOutcome = 'occurred' | 'prevented' | 'false_alarm';

// Prediction List Response
export interface PredictionListResponse {
  items: Prediction[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Prediction Statistics Response
export interface PredictionStatsResponse {
  total_predictions: number;
  active_predictions: number;
  accuracy_rate: number;
  by_severity: Record<PredictionSeverity, number>;
  by_type: Record<PredictionType, number>;
  by_outcome: Record<ActualOutcome, number>;
}

// Vulnerability Entity
export interface Vulnerability {
  id: string;
  api_id: string;
  vulnerability_type: VulnerabilityType;
  severity: VulnerabilitySeverity;
  category: VulnerabilityCategory;
  title: string;
  description: string;
  cve_id?: string;
  cvss_score?: number;
  affected_endpoints: string[];
  remediation: string;
  remediation_type?: RemediationType;
  remediation_actions?: RemediationAction[];
  status: VulnerabilityStatus;
  detected_at: string;
  resolved_at?: string;
  compliance_violations?: ComplianceStandard[];
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export type VulnerabilityType = 'authentication' | 'authorization' | 'injection' | 'data_exposure' | 'configuration' | 'dependency' | 'compliance' | 'data_protection' | 'other';
export type VulnerabilitySeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type VulnerabilityCategory = 'authentication' | 'authorization' | 'injection' | 'data_exposure' | 'configuration' | 'dependency' | 'other';
export type VulnerabilityStatus = 'open' | 'in_progress' | 'remediated' | 'verified' | 'false_positive' | 'accepted_risk';
export type RemediationType = 'automated' | 'manual' | 'assisted';
export type ComplianceStandard = 'GDPR' | 'HIPAA' | 'PCI_DSS' | 'SOC2' | 'ISO_27001';

export interface RemediationAction {
  action: string;
  type: string;
  status: 'pending' | 'completed' | 'failed';
  performed_at?: string;
  performed_by?: string;
  gateway_policy_id?: string;
  error_message?: string;
}

// Security Posture
export interface SecurityPosture {
  total_vulnerabilities: number;
  by_severity: Record<VulnerabilitySeverity, number>;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  remediation_rate: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  avg_remediation_time_ms?: number;
  compliance_issues?: ComplianceIssue[];
}

export interface ComplianceIssue {
  standard: ComplianceStandard;
  affected_apis: number;
  severity: VulnerabilitySeverity;
  description: string;
}

// Scan Response
export interface ScanResponse {
  scan_id: string;
  api_id: string;
  api_name: string;
  scan_completed_at: string;
  vulnerabilities_found: number;
  severity_breakdown: Record<VulnerabilitySeverity, number>;
  vulnerabilities: Vulnerability[];
  remediation_plan: Record<string, any>;
  ai_enhanced: boolean;
  compliance_issues?: ComplianceStandard[];
}

// Remediation Response
export interface RemediationResponse {
  vulnerability_id: string;
  status: string;
  remediation_result?: Record<string, any>;
  verification_result?: Record<string, any>;
  message?: string;
}

// Recommendation Entity
export interface Recommendation {
  id: string;
  api_id: string;
  api_name?: string;
  recommendation_type: RecommendationType;
  title: string;
  description: string;
  priority: RecommendationPriority;
  estimated_impact: EstimatedImpact;
  implementation_effort: ImplementationEffort;
  implementation_steps: string[];
  status: RecommendationStatus;
  implemented_at?: string;
  cost_savings?: number;
  created_at: string;
  updated_at: string;
  expires_at?: string;
}

export interface EstimatedImpact {
  metric: string;
  current_value: number;
  expected_value: number;
  improvement_percentage: number;
  confidence: number;
}

export type RecommendationType = 'caching' | 'rate_limiting' | 'compression';
export type RecommendationPriority = 'critical' | 'high' | 'medium' | 'low';
export type RecommendationStatus = 'pending' | 'in_progress' | 'implemented' | 'rejected' | 'expired';
export type ImplementationEffort = 'low' | 'medium' | 'high';

// Recommendation List Response
export interface RecommendationListResponse {
  recommendations: Recommendation[];
  total: number;
  page: number;
  page_size: number;
}

// Recommendation Statistics Response
export interface RecommendationStatsResponse {
  total_recommendations: number;
  by_status: Array<{ status: string; count: number }>;
  by_priority: Array<{ priority: string; count: number }>;
  by_type: Array<{ type: string; count: number }>;
  avg_improvement: number;
  total_cost_savings: number;
}

// Rate Limit Policy Entity
export interface RateLimitPolicy {
  id: string;
  api_id: string;
  api_name?: string;
  policy_name: string;
  policy_type: PolicyType;
  status: PolicyStatus;
  limit_thresholds: LimitThresholds;
  priority_rules?: PriorityRule[];
  burst_allowance?: number;
  adaptation_parameters?: AdaptationParameters;
  consumer_tiers?: ConsumerTier[];
  enforcement_action: EnforcementAction;
  applied_at?: string;
  last_adjusted_at?: string;
  effectiveness_score?: number;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LimitThresholds {
  requests_per_second?: number;
  requests_per_minute?: number;
  requests_per_hour?: number;
  concurrent_requests?: number;
}

export interface PriorityRule {
  tier: string;
  multiplier: number;
  guaranteed_throughput: number;
  burst_multiplier: number;
}

export interface AdaptationParameters {
  learning_rate: number;
  adjustment_frequency: number;
  min_threshold?: number;
  max_threshold?: number;
}

export interface ConsumerTier {
  tier_name: string;
  tier_level: number;
  rate_multiplier: number;
  priority_score: number;
}

export type PolicyType = 'fixed' | 'adaptive' | 'priority_based' | 'burst_allowance';
export type PolicyStatus = 'active' | 'inactive' | 'testing';
export type EnforcementAction = 'throttle' | 'reject' | 'queue';

// Rate Limit Policy List Response
export interface RateLimitPolicyListResponse {
  policies: RateLimitPolicy[];
  total: number;
  page: number;
  page_size: number;
}

// Rate Limit Effectiveness Response
export interface RateLimitEffectivenessResponse {
  policy_id: string;
  api_id: string;
  effectiveness_score: number;
  metrics: {
    error_rate: number;
    avg_response_time: number;
    throttled_requests: number;
    total_requests: number;
  };
  recommendations: string[];
  analysis_period: {
    start: string;
    end: string;
  };
}

// Rate Limit Suggestion Response
export interface RateLimitSuggestionResponse {
  api_id: string;
  suggested_policy: {
    policy_type: PolicyType;
    limit_thresholds: LimitThresholds;
    enforcement_action: EnforcementAction;
  };
  reasoning: string;
  traffic_analysis: {
    avg_throughput: number;
    peak_throughput: number;
    p95_throughput: number;
    coefficient_of_variation: number;
  };
}

// Query History Entity
export interface QueryHistory {
  id: string;
  query_text: string;
  query_type: QueryType;
  results_count: number;
  execution_time_ms: number;
  status: QueryStatus;
  error_message?: string;
  created_at: string;
}

export type QueryType = 'discovery' | 'metrics' | 'security' | 'recommendations' | 'general';
export type QueryStatus = 'success' | 'error' | 'timeout';

// Dashboard Statistics
export interface DashboardStats {
  total_apis: number;
  active_apis: number;
  shadow_apis: number;
  total_gateways: number;
  active_gateways: number;
  avg_health_score: number;
  avg_response_time: number;
  total_requests_24h: number;
  error_rate_24h: number;
  critical_vulnerabilities: number;
  high_priority_recommendations: number;
}

// Generic Paginated Response
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip?: number;
  limit?: number;
}

// API List Response
export interface APIListResponse {
  items: API[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Gateway List Response
export interface GatewayListResponse {
  items: Gateway[];
  total: number;
}

// Metrics Time Series Response
export interface MetricsTimeSeriesResponse {
  api_id: string;
  start: string;
  end: string;
  interval_minutes: number;
  data_points: number;
  metrics: TimeSeriesDataPoint[];
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  response_time_p50: number;
  response_time_p95: number;
  response_time_p99: number;
  error_rate: number;
  throughput: number;
  availability: number;
  sample_count?: number;
}

// Made with Bob