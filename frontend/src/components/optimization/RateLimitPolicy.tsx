import { Shield, Activity, TrendingUp, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import type { RateLimitPolicy, PolicyType, PolicyStatus, EnforcementAction } from '../../types';

interface RateLimitPolicyProps {
  policy: RateLimitPolicy;
  onActivate?: (policyId: string) => void;
  onDeactivate?: (policyId: string) => void;
  detailed?: boolean;
}

/**
 * RateLimitPolicy Component
 * 
 * Displays a rate limit policy with:
 * - Policy name, type, and status
 * - Limit thresholds (RPS, RPM, RPH, concurrent)
 * - Enforcement action and effectiveness score
 * - Priority rules and consumer tiers (if applicable)
 * - Activation/deactivation controls
 */
const RateLimitPolicy = ({ policy, onActivate, onDeactivate, detailed = false }: RateLimitPolicyProps) => {
  // Policy type display name
  const getPolicyTypeDisplayName = (type: PolicyType) => {
    switch (type) {
      case 'fixed': return 'Fixed';
      case 'adaptive': return 'Adaptive';
      case 'priority_based': return 'Priority-Based';
      case 'burst_allowance': return 'Burst Allowance';
      default: return type;
    }
  };

  // Status badge color
  const getStatusColor = (status: PolicyStatus) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'testing': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Status icon
  const getStatusIcon = (status: PolicyStatus) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4" />;
      case 'inactive': return <AlertCircle className="w-4 h-4" />;
      case 'testing': return <Activity className="w-4 h-4" />;
      default: return <AlertCircle className="w-4 h-4" />;
    }
  };

  // Enforcement action display
  const getEnforcementActionDisplay = (action: EnforcementAction) => {
    switch (action) {
      case 'throttle': return { text: 'Throttle', color: 'text-yellow-600', icon: <Clock className="w-4 h-4" /> };
      case 'reject': return { text: 'Reject', color: 'text-red-600', icon: <AlertCircle className="w-4 h-4" /> };
      case 'queue': return { text: 'Queue', color: 'text-blue-600', icon: <Activity className="w-4 h-4" /> };
      default: return { text: action, color: 'text-gray-600', icon: <AlertCircle className="w-4 h-4" /> };
    }
  };

  const enforcementDisplay = getEnforcementActionDisplay(policy.enforcement_action);

  // Format threshold display
  const formatThreshold = (value: number | undefined, unit: string) => {
    if (value === undefined) return null;
    return `${value.toLocaleString()} ${unit}`;
  };

  if (detailed) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{policy.policy_name}</h3>
              <div className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(policy.status)} flex items-center gap-1`}>
                  {getStatusIcon(policy.status)}
                  {policy.status.toUpperCase()}
                </span>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                  {getPolicyTypeDisplayName(policy.policy_type)}
                </span>
              </div>
            </div>
            <Shield className="w-8 h-8 text-blue-500" />
          </div>

          {/* Effectiveness Score */}
          {policy.effectiveness_score !== undefined && (
            <div className="mt-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Effectiveness Score</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-green-500 to-blue-500"
                      style={{ width: `${policy.effectiveness_score * 100}%` }}
                    />
                  </div>
                  <span className="text-lg font-bold text-blue-600">
                    {(policy.effectiveness_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Limit Thresholds */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-3">Limit Thresholds</h4>
          <div className="grid grid-cols-2 gap-4">
            {policy.limit_thresholds.requests_per_second && (
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Requests per Second</p>
                <p className="text-2xl font-bold text-gray-900">
                  {policy.limit_thresholds.requests_per_second.toLocaleString()}
                </p>
              </div>
            )}
            {policy.limit_thresholds.requests_per_minute && (
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Requests per Minute</p>
                <p className="text-2xl font-bold text-gray-900">
                  {policy.limit_thresholds.requests_per_minute.toLocaleString()}
                </p>
              </div>
            )}
            {policy.limit_thresholds.requests_per_hour && (
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Requests per Hour</p>
                <p className="text-2xl font-bold text-gray-900">
                  {policy.limit_thresholds.requests_per_hour.toLocaleString()}
                </p>
              </div>
            )}
            {policy.limit_thresholds.concurrent_requests && (
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Concurrent Requests</p>
                <p className="text-2xl font-bold text-gray-900">
                  {policy.limit_thresholds.concurrent_requests.toLocaleString()}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Enforcement & Burst */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-3">Configuration</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-2">Enforcement Action</p>
              <div className={`flex items-center gap-2 ${enforcementDisplay.color} font-semibold`}>
                {enforcementDisplay.icon}
                <span>{enforcementDisplay.text}</span>
              </div>
            </div>
            {policy.burst_allowance && (
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Burst Allowance</p>
                <p className="text-xl font-bold text-gray-900">
                  {policy.burst_allowance.toLocaleString()} requests
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Priority Rules */}
        {policy.priority_rules && policy.priority_rules.length > 0 && (
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-gray-900 mb-3">Priority Rules</h4>
            <div className="space-y-2">
              {policy.priority_rules.map((rule, index) => (
                <div key={index} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gray-900 capitalize">{rule.tier}</span>
                    <span className="text-sm text-gray-600">Multiplier: {rule.multiplier}x</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                    <div>Guaranteed: {rule.guaranteed_throughput} req/s</div>
                    <div>Burst: {rule.burst_multiplier}x</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Adaptation Parameters */}
        {policy.adaptation_parameters && (
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-gray-900 mb-3">Adaptation Parameters</h4>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Learning Rate:</span>
                  <span className="ml-2 font-semibold text-gray-900">
                    {(policy.adaptation_parameters.learning_rate * 100).toFixed(0)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Adjustment Frequency:</span>
                  <span className="ml-2 font-semibold text-gray-900">
                    {policy.adaptation_parameters.adjustment_frequency}s
                  </span>
                </div>
                {policy.adaptation_parameters.min_threshold && (
                  <div>
                    <span className="text-gray-600">Min Threshold:</span>
                    <span className="ml-2 font-semibold text-gray-900">
                      {policy.adaptation_parameters.min_threshold}
                    </span>
                  </div>
                )}
                {policy.adaptation_parameters.max_threshold && (
                  <div>
                    <span className="text-gray-600">Max Threshold:</span>
                    <span className="ml-2 font-semibold text-gray-900">
                      {policy.adaptation_parameters.max_threshold}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Timestamps */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-3">Timeline</h4>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Created:</span>
              <span className="font-medium">{new Date(policy.created_at).toLocaleString()}</span>
            </div>
            {policy.applied_at && (
              <div className="flex justify-between">
                <span>Applied:</span>
                <span className="font-medium">{new Date(policy.applied_at).toLocaleString()}</span>
              </div>
            )}
            {policy.last_adjusted_at && (
              <div className="flex justify-between">
                <span>Last Adjusted:</span>
                <span className="font-medium">{new Date(policy.last_adjusted_at).toLocaleString()}</span>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          {policy.status === 'inactive' && onActivate && (
            <button
              onClick={() => onActivate(policy.id)}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
            >
              <CheckCircle className="w-5 h-5" />
              Activate Policy
            </button>
          )}
          {policy.status === 'active' && onDeactivate && (
            <button
              onClick={() => onDeactivate(policy.id)}
              className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
            >
              <AlertCircle className="w-5 h-5" />
              Deactivate Policy
            </button>
          )}
        </div>
      </div>
    );
  }

  // Compact view
  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{policy.policy_name}</h3>
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(policy.status)} flex items-center gap-1`}>
              {getStatusIcon(policy.status)}
              {policy.status.toUpperCase()}
            </span>
            <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              {getPolicyTypeDisplayName(policy.policy_type)}
            </span>
          </div>
        </div>
        <Shield className="w-6 h-6 text-blue-500" />
      </div>

      {/* Thresholds Summary */}
      <div className="bg-gray-50 rounded-lg p-3 mb-4">
        <div className="grid grid-cols-2 gap-2 text-sm">
          {policy.limit_thresholds.requests_per_second && (
            <div>
              <span className="text-gray-600">RPS:</span>
              <span className="ml-1 font-semibold text-gray-900">
                {policy.limit_thresholds.requests_per_second}
              </span>
            </div>
          )}
          {policy.limit_thresholds.requests_per_minute && (
            <div>
              <span className="text-gray-600">RPM:</span>
              <span className="ml-1 font-semibold text-gray-900">
                {policy.limit_thresholds.requests_per_minute}
              </span>
            </div>
          )}
          {policy.limit_thresholds.requests_per_hour && (
            <div>
              <span className="text-gray-600">RPH:</span>
              <span className="ml-1 font-semibold text-gray-900">
                {policy.limit_thresholds.requests_per_hour.toLocaleString()}
              </span>
            </div>
          )}
          {policy.limit_thresholds.concurrent_requests && (
            <div>
              <span className="text-gray-600">Concurrent:</span>
              <span className="ml-1 font-semibold text-gray-900">
                {policy.limit_thresholds.concurrent_requests}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Enforcement & Effectiveness */}
      <div className="flex items-center justify-between text-sm">
        <div className={`flex items-center gap-1 ${enforcementDisplay.color} font-medium`}>
          {enforcementDisplay.icon}
          <span>{enforcementDisplay.text}</span>
        </div>
        {policy.effectiveness_score !== undefined && (
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <span className="font-semibold text-gray-900">
              {(policy.effectiveness_score * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default RateLimitPolicy;

// Made with Bob