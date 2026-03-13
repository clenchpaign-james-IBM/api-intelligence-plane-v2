// Force rebuild - Rate Limiting Apply Feature v2
import { Shield, Activity, TrendingUp, AlertCircle, CheckCircle, Clock, Zap } from '../../utils/carbonIcons';
import { Tile, Tag, Button } from '@carbon/react';
import type { RateLimitPolicy, PolicyType, PolicyStatus, EnforcementAction } from '../../types';

interface RateLimitPolicyProps {
  policy: RateLimitPolicy;
  onActivate?: (policyId: string) => void;
  onDeactivate?: (policyId: string) => void;
  onApply?: (policyId: string) => void;
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
const RateLimitPolicy = ({ policy, onActivate, onDeactivate, onApply, detailed = false }: RateLimitPolicyProps) => {
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

  // Status tag type
  const getStatusTagType = (status: PolicyStatus): 'green' | 'gray' | 'blue' => {
    switch (status) {
      case 'active': return 'green';
      case 'inactive': return 'gray';
      case 'testing': return 'blue';
      default: return 'gray';
    }
  };

  // Status icon
  const getStatusIcon = (status: PolicyStatus) => {
    switch (status) {
      case 'active': return <CheckCircle size={16} style={{ color: 'var(--cds-support-success)' }} />;
      case 'inactive': return <AlertCircle size={16} style={{ color: 'var(--cds-icon-secondary)' }} />;
      case 'testing': return <Activity size={16} style={{ color: 'var(--cds-support-info)' }} />;
      default: return <AlertCircle size={16} style={{ color: 'var(--cds-icon-secondary)' }} />;
    }
  };

  // Enforcement action display
  const getEnforcementActionDisplay = (action: EnforcementAction) => {
    switch (action) {
      case 'throttle': return { text: 'Throttle', color: 'var(--cds-support-warning)', icon: <Clock size={16} /> };
      case 'reject': return { text: 'Reject', color: 'var(--cds-support-error)', icon: <AlertCircle size={16} /> };
      case 'queue': return { text: 'Queue', color: 'var(--cds-support-info)', icon: <Activity size={16} /> };
      default: return { text: action, color: 'var(--cds-text-secondary)', icon: <AlertCircle size={16} /> };
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
      <Tile style={{ padding: 'var(--cds-spacing-07)', border: '1px solid var(--cds-border-subtle)', borderRadius: '4px' }}>
        {/* Header */}
        <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 'var(--cds-spacing-04)' }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-03)' }}>{policy.policy_name}</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
                <Tag type={getStatusTagType(policy.status)} size="md" renderIcon={() => getStatusIcon(policy.status)}>
                  {policy.status.toUpperCase()}
                </Tag>
                <Tag type="purple" size="md">
                  {getPolicyTypeDisplayName(policy.policy_type)}
                </Tag>
              </div>
            </div>
            <Shield size={32} style={{ color: 'var(--cds-link-primary)' }} />
          </div>

          {/* Effectiveness Score */}
          {policy.effectiveness_score !== undefined && (
            <div style={{ marginTop: 'var(--cds-spacing-05)', backgroundColor: 'var(--cds-layer-accent)', borderRadius: '4px', padding: 'var(--cds-spacing-05)', border: '1px solid var(--cds-border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--cds-text-secondary)' }}>Effectiveness Score</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
                  <div style={{ width: '128px', height: '8px', backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        background: 'linear-gradient(to right, var(--cds-support-success), var(--cds-support-info))',
                        width: `${policy.effectiveness_score * 100}%`
                      }}
                    />
                  </div>
                  <span style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-link-primary)' }}>
                    {(policy.effectiveness_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Limit Thresholds */}
        <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
          <h4 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-04)' }}>Limit Thresholds</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--cds-spacing-05)' }}>
            {policy.limit_thresholds.requests_per_second && (
              <div style={{ backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px', padding: 'var(--cds-spacing-05)', border: '1px solid var(--cds-border-subtle)' }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Requests per Second</p>
                <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                  {policy.limit_thresholds.requests_per_second.toLocaleString()}
                </p>
              </div>
            )}
            {policy.limit_thresholds.requests_per_minute && (
              <div style={{ backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px', padding: 'var(--cds-spacing-05)', border: '1px solid var(--cds-border-subtle)' }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Requests per Minute</p>
                <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                  {policy.limit_thresholds.requests_per_minute.toLocaleString()}
                </p>
              </div>
            )}
            {policy.limit_thresholds.requests_per_hour && (
              <div style={{ backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px', padding: 'var(--cds-spacing-05)', border: '1px solid var(--cds-border-subtle)' }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Requests per Hour</p>
                <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                  {policy.limit_thresholds.requests_per_hour.toLocaleString()}
                </p>
              </div>
            )}
            {policy.limit_thresholds.concurrent_requests && (
              <div style={{ backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px', padding: 'var(--cds-spacing-05)', border: '1px solid var(--cds-border-subtle)' }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Concurrent Requests</p>
                <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                  {policy.limit_thresholds.concurrent_requests.toLocaleString()}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Enforcement & Burst */}
        <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
          <h4 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-04)' }}>Configuration</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--cds-spacing-05)' }}>
            <div style={{ backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px', padding: 'var(--cds-spacing-05)', border: '1px solid var(--cds-border-subtle)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-03)' }}>Enforcement Action</p>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)', color: enforcementDisplay.color, fontWeight: 600 }}>
                {enforcementDisplay.icon}
                <span>{enforcementDisplay.text}</span>
              </div>
            </div>
            {policy.burst_allowance && (
              <div style={{ backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px', padding: 'var(--cds-spacing-05)', border: '1px solid var(--cds-border-subtle)' }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Burst Allowance</p>
                <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
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
        <div style={{ display: 'flex', gap: 'var(--cds-spacing-04)' }}>
          {policy.status === 'inactive' && onActivate && (
            <Button
              kind="primary"
              renderIcon={CheckCircle}
              onClick={() => onActivate(policy.id)}
              style={{ flex: 1 }}
            >
              Activate Policy
            </Button>
          )}
          {policy.status === 'active' && onDeactivate && (
            <Button
              kind="secondary"
              renderIcon={AlertCircle}
              onClick={() => onDeactivate(policy.id)}
              style={{ flex: 1 }}
            >
              Deactivate Policy
            </Button>
          )}
          {(policy.status === 'active' || policy.status === 'inactive') && onApply && (
            <Button
              kind="tertiary"
              renderIcon={Zap}
              onClick={() => onApply(policy.id)}
              style={{ flex: 1 }}
            >
              Apply to Gateway
            </Button>
          )}
        </div>
      </Tile>
    );
  }

  // Compact view
  return (
    <Tile style={{ padding: 'var(--cds-spacing-06)', border: '1px solid var(--cds-border-subtle)', borderRadius: '4px', cursor: 'pointer' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 'var(--cds-spacing-05)' }}>
        <div style={{ flex: 1 }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-03)' }}>{policy.policy_name}</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
            <Tag type={getStatusTagType(policy.status)} size="sm" renderIcon={() => getStatusIcon(policy.status)}>
              {policy.status.toUpperCase()}
            </Tag>
            <Tag type="purple" size="sm">
              {getPolicyTypeDisplayName(policy.policy_type)}
            </Tag>
          </div>
        </div>
        <Shield size={24} style={{ color: 'var(--cds-link-primary)' }} />
      </div>

      {/* Thresholds Summary */}
      <div style={{ backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px', padding: 'var(--cds-spacing-04)', marginBottom: 'var(--cds-spacing-05)', border: '1px solid var(--cds-border-subtle)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--cds-spacing-03)', fontSize: '0.875rem' }}>
          {policy.limit_thresholds.requests_per_second && (
            <div>
              <span style={{ color: 'var(--cds-text-secondary)' }}>RPS:</span>
              <span style={{ marginLeft: 'var(--cds-spacing-02)', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {policy.limit_thresholds.requests_per_second}
              </span>
            </div>
          )}
          {policy.limit_thresholds.requests_per_minute && (
            <div>
              <span style={{ color: 'var(--cds-text-secondary)' }}>RPM:</span>
              <span style={{ marginLeft: 'var(--cds-spacing-02)', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {policy.limit_thresholds.requests_per_minute}
              </span>
            </div>
          )}
          {policy.limit_thresholds.requests_per_hour && (
            <div>
              <span style={{ color: 'var(--cds-text-secondary)' }}>RPH:</span>
              <span style={{ marginLeft: 'var(--cds-spacing-02)', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {policy.limit_thresholds.requests_per_hour.toLocaleString()}
              </span>
            </div>
          )}
          {policy.limit_thresholds.concurrent_requests && (
            <div>
              <span style={{ color: 'var(--cds-text-secondary)' }}>Concurrent:</span>
              <span style={{ marginLeft: 'var(--cds-spacing-02)', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {policy.limit_thresholds.concurrent_requests}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Enforcement & Effectiveness */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: 'var(--cds-spacing-05)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-02)', color: enforcementDisplay.color, fontWeight: 500 }}>
          {enforcementDisplay.icon}
          <span>{enforcementDisplay.text}</span>
        </div>
        {policy.effectiveness_score !== undefined && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
            <TrendingUp size={16} style={{ color: 'var(--cds-support-success)' }} />
            <span style={{ fontWeight: 600, color: 'var(--cds-text-primary)' }}>
              {(policy.effectiveness_score * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 'var(--cds-spacing-03)' }}>
        {policy.status === 'inactive' && onActivate && (
          <Button
            kind="primary"
            size="sm"
            renderIcon={CheckCircle}
            onClick={() => onActivate(policy.id)}
            style={{ flex: 1 }}
          >
            Activate
          </Button>
        )}
        {policy.status === 'active' && onDeactivate && (
          <Button
            kind="secondary"
            size="sm"
            renderIcon={AlertCircle}
            onClick={() => onDeactivate(policy.id)}
            style={{ flex: 1 }}
          >
            Deactivate
          </Button>
        )}
        {(policy.status === 'active' || policy.status === 'inactive') && onApply && (
          <Button
            kind="tertiary"
            size="sm"
            renderIcon={Zap}
            onClick={() => onApply(policy.id)}
            style={{ flex: 1 }}
          >
            Apply
          </Button>
        )}
      </div>
    </Tile>
  );
};

export default RateLimitPolicy;

// Made with Bob