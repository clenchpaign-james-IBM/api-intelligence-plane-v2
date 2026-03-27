/**
 * API Security Card Component
 * 
 * Displays an API with its security vulnerabilities and metrics.
 * This is the primary component for the API-centric security view.
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import type { API, Vulnerability } from '../../types';
import { VulnerabilityCard } from './VulnerabilityCard';
import { getSeverityColor } from '../../services/security';

interface APISecurityCardProps {
  api: API;
  vulnerabilities: Vulnerability[];
  onRemediate?: () => void;
}

export const APISecurityCard: React.FC<APISecurityCardProps> = ({
  api,
  vulnerabilities,
  onRemediate,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Calculate security metrics
  const criticalCount = vulnerabilities.filter(v => v.severity === 'critical').length;
  const highCount = vulnerabilities.filter(v => v.severity === 'high').length;
  const mediumCount = vulnerabilities.filter(v => v.severity === 'medium').length;
  const lowCount = vulnerabilities.filter(v => v.severity === 'low').length;
  const totalCount = vulnerabilities.length;

  const openCount = vulnerabilities.filter(v => v.status === 'open').length;
  const inProgressCount = vulnerabilities.filter(v => v.status === 'in_progress').length;
  const remediatedCount = vulnerabilities.filter(v => v.status === 'remediated').length;

  // Calculate risk score (0-100, higher is worse)
  const riskScore = Math.min(
    criticalCount * 40 + highCount * 25 + mediumCount * 15 + lowCount * 5,
    100
  );

  const getRiskLevel = (score: number): string => {
    if (score >= 75) return 'Critical';
    if (score >= 50) return 'High';
    if (score >= 25) return 'Medium';
    return 'Low';
  };

  const getRiskColor = (score: number): string => {
    if (score >= 75) return 'text-red-600 bg-red-50 border-red-200';
    if (score >= 50) return 'text-orange-600 bg-orange-50 border-orange-200';
    if (score >= 25) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-green-600 bg-green-50 border-green-200';
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
      {/* API Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <svg
                className="h-6 w-6 text-blue-600 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <div className="flex-1 min-w-0">
                <Link
                  to={`/apis/${api.id}`}
                  className="text-lg font-bold text-gray-900 hover:text-blue-600 transition-colors"
                >
                  {api.name}
                </Link>
                <p className="text-xs text-gray-600">
                  {api.base_path} • {api.methods.join(', ')} • {api.endpoints.length} endpoints
                </p>
              </div>
            </div>
            
            {/* API Tags */}
            {api.tags && api.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {api.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 text-xs bg-white text-gray-700 rounded border border-gray-300"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Risk Score */}
          <div className={`ml-4 px-4 py-2 rounded-lg border-2 ${getRiskColor(riskScore)} flex-shrink-0`}>
            <div className="text-center">
              <div className="text-2xl font-bold">{riskScore}</div>
              <div className="text-xs font-medium">Risk Score</div>
              <div className="text-xs">{getRiskLevel(riskScore)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Security Policies Summary */}
      {api.security_policies && (
        <div className="px-6 py-3 bg-blue-50 border-b border-blue-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span className="text-sm font-medium text-blue-900">Security Policies Active</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {api.security_policies.authentication_required && (
                <span className="px-1.5 py-0.5 text-xs bg-green-100 text-green-800 rounded">Auth</span>
              )}
              {api.security_policies.tls_enforced && (
                <span className="px-1.5 py-0.5 text-xs bg-green-100 text-green-800 rounded">
                  {api.security_policies.tls_version || 'TLS'}
                </span>
              )}
              {api.security_policies.rate_limiting_enabled && (
                <span className="px-1.5 py-0.5 text-xs bg-green-100 text-green-800 rounded">Rate Limit</span>
              )}
              {api.security_policies.waf_enabled && (
                <span className="px-1.5 py-0.5 text-xs bg-green-100 text-green-800 rounded">WAF</span>
              )}
              {api.security_policies.compliance_standards && api.security_policies.compliance_standards.length > 0 && (
                <span className="px-1.5 py-0.5 text-xs bg-purple-100 text-purple-800 rounded">
                  {api.security_policies.compliance_standards.join(', ')}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Security Metrics */}
      <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* Total Vulnerabilities */}
          <div className="text-center">
            <div className="text-xl font-bold text-gray-900">{totalCount}</div>
            <div className="text-xs text-gray-600">Total</div>
          </div>

          {/* By Severity */}
          <div className="text-center">
            <div className="flex justify-center flex-wrap gap-1">
              {criticalCount > 0 && (
                <span className="px-1.5 py-0.5 text-xs font-medium bg-red-100 text-red-800 rounded">
                  {criticalCount} Crit
                </span>
              )}
              {highCount > 0 && (
                <span className="px-1.5 py-0.5 text-xs font-medium bg-orange-100 text-orange-800 rounded">
                  {highCount} High
                </span>
              )}
              {mediumCount > 0 && (
                <span className="px-1.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">
                  {mediumCount} Med
                </span>
              )}
              {lowCount > 0 && (
                <span className="px-1.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                  {lowCount} Low
                </span>
              )}
            </div>
          </div>

          {/* By Status */}
          <div className="text-center">
            <div className="text-xl font-bold text-red-600">{openCount}</div>
            <div className="text-xs text-gray-600">Open</div>
          </div>

          <div className="text-center">
            <div className="text-xl font-bold text-green-600">{remediatedCount}</div>
            <div className="text-xs text-gray-600">Fixed</div>
          </div>
        </div>
      </div>

      {/* Vulnerabilities Section */}
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-3">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-1.5 text-left font-medium text-gray-900 hover:text-blue-600 transition-colors"
          >
            <span className="text-sm">
              {isExpanded ? 'Hide' : 'Show'} Vulnerabilities ({totalCount})
            </span>
            <svg
              className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
          
          {/* Security Policy Details Toggle */}
          {api.security_policies && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center space-x-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>View Policy Details</span>
            </button>
          )}
        </div>

        {/* Security Policy Details */}
        {isExpanded && api.security_policies && (
          <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="text-xs font-semibold text-blue-900 mb-2">Security Policy Configuration</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
              <PolicyItem
                label="Authentication"
                enabled={api.security_policies.authentication_required}
              />
              <PolicyItem
                label="Authorization"
                enabled={api.security_policies.authorization_enabled}
              />
              <PolicyItem
                label="Rate Limiting"
                enabled={api.security_policies.rate_limiting_enabled}
                detail={api.security_policies.rate_limit_config ?
                  `${api.security_policies.rate_limit_config.requests_per_minute} req/min` : undefined}
              />
              <PolicyItem
                label="TLS/HTTPS"
                enabled={api.security_policies.tls_enforced}
                detail={api.security_policies.tls_version}
              />
              <PolicyItem
                label="CORS"
                enabled={api.security_policies.cors_enabled}
              />
              <PolicyItem
                label="Input Validation"
                enabled={api.security_policies.input_validation_enabled}
              />
              <PolicyItem
                label="Output Sanitization"
                enabled={api.security_policies.output_sanitization_enabled}
              />
              <PolicyItem
                label="Encryption at Rest"
                enabled={api.security_policies.encryption_at_rest}
              />
              <PolicyItem
                label="WAF"
                enabled={api.security_policies.waf_enabled}
              />
              <PolicyItem
                label="IP Whitelisting"
                enabled={api.security_policies.ip_whitelisting_enabled}
              />
              <PolicyItem
                label="Key Rotation"
                enabled={api.security_policies.api_key_rotation_enabled}
                detail={api.security_policies.key_rotation_days ?
                  `Every ${api.security_policies.key_rotation_days} days` : undefined}
              />
              <PolicyItem
                label="Security Logging"
                enabled={api.security_policies.logging_enabled}
              />
            </div>
            {api.security_policies.last_policy_update && (
              <p className="mt-2 text-xs text-gray-600">
                Last updated: {new Date(api.security_policies.last_policy_update).toLocaleDateString()}
              </p>
            )}
          </div>
        )}

        {/* Vulnerabilities List */}
        <div>
        {isExpanded && (
          <div className="space-y-3">
            {vulnerabilities.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <svg
                  className="mx-auto h-12 w-12 text-green-400 mb-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p>No vulnerabilities found for this API</p>
              </div>
            ) : (
              vulnerabilities.map((vulnerability) => (
                <VulnerabilityCard
                  key={vulnerability.id}
                  vulnerability={vulnerability}
                  apiName={api.name}
                  onRemediate={onRemediate}
                />
              ))
            )}
          </div>
        )}
        </div>
      </div>
    </div>
  );
};

// Helper component for policy items
const PolicyItem: React.FC<{ label: string; enabled: boolean; detail?: string }> = ({
  label,
  enabled,
  detail
}) => (
  <div className="flex items-center space-x-2">
    {enabled ? (
      <svg className="w-4 h-4 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ) : (
      <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    )}
    <div className="flex-1 min-w-0">
      <span className={`text-xs font-medium ${enabled ? 'text-gray-900' : 'text-gray-500'}`}>
        {label}
      </span>
      {detail && (
        <span className="ml-1 text-xs text-gray-600">({detail})</span>
      )}
    </div>
  </div>
);

// Made with Bob