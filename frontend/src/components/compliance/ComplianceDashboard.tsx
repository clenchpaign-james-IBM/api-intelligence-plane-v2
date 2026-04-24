/**
 * Compliance Dashboard Component
 *
 * Displays overall compliance posture metrics and compliance score with interactive filtering.
 */

import React from 'react';
import type { 
  CompliancePosture, 
  ComplianceStandard, 
  ComplianceSeverity, 
  ComplianceStatus 
} from '../../types';

interface ComplianceDashboardProps {
  posture: CompliancePosture;
  onFilterByStandard?: (standard: ComplianceStandard) => void;
  onFilterBySeverity?: (severity: ComplianceSeverity) => void;
  onFilterByStatus?: (status: ComplianceStatus) => void;
  onViewAllViolations?: () => void;
}

export const ComplianceDashboard: React.FC<ComplianceDashboardProps> = ({
  posture,
  onFilterByStandard,
  onFilterBySeverity,
  onFilterByStatus,
  onViewAllViolations,
}) => {
  const severityOrder: ComplianceSeverity[] = ['critical', 'high', 'medium', 'low'];
  const standardOrder: ComplianceStandard[] = ['GDPR', 'HIPAA', 'SOC2', 'PCI_DSS', 'ISO_27001'];

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Compliance Posture</h2>

      {/* Compliance Score */}
      <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Overall Compliance Score</h3>
            <p className="text-sm text-gray-600">
              Based on violations across all regulatory standards
            </p>
          </div>
          <div className="text-center">
            <div className={`text-6xl font-bold ${getComplianceScoreColor(posture.overall_score)}`}>
              {posture.overall_score}
            </div>
            <div className="text-sm font-medium text-gray-600 mt-2">
              Risk Level: <span className={getRiskLevelColor(posture.risk_level)}>
                {posture.risk_level.toUpperCase()}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <button
          onClick={onViewAllViolations}
          className="p-4 bg-blue-50 rounded-lg border border-blue-200 hover:bg-blue-100 hover:shadow-md transition-all text-left cursor-pointer"
        >
          <div className="text-sm font-medium text-blue-700 mb-1">Total Violations</div>
          <div className="text-3xl font-bold text-blue-900">{posture.total_violations}</div>
          {onViewAllViolations && (
            <div className="text-xs text-blue-600 mt-2">Click to view all →</div>
          )}
        </button>

        <button
          onClick={() => onFilterByStatus?.('open')}
          className="p-4 bg-orange-50 rounded-lg border border-orange-200 hover:bg-orange-100 hover:shadow-md transition-all text-left cursor-pointer"
        >
          <div className="text-sm font-medium text-orange-700 mb-1">Open Violations</div>
          <div className="text-3xl font-bold text-orange-900">{posture.open_violations}</div>
          {onFilterByStatus && (
            <div className="text-xs text-orange-600 mt-2">Click to view →</div>
          )}
        </button>

        <button
          onClick={() => onFilterByStatus?.('resolved')}
          className="p-4 bg-green-50 rounded-lg border border-green-200 hover:bg-green-100 hover:shadow-md transition-all text-left cursor-pointer"
        >
          <div className="text-sm font-medium text-green-700 mb-1">Resolved Violations</div>
          <div className="text-3xl font-bold text-green-900">{posture.resolved_violations}</div>
          {onFilterByStatus && (
            <div className="text-xs text-green-600 mt-2">Click to view →</div>
          )}
        </button>
      </div>

      {/* Last Scan & Next Audit */}
      <div className="mb-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm font-medium text-gray-600 mb-1">Last Scan Date</div>
            <div className="text-lg font-semibold text-gray-900">
              {new Date(posture.last_scan_date).toLocaleDateString()}
            </div>
          </div>
          {posture.next_audit_date && (
            <div>
              <div className="text-sm font-medium text-gray-600 mb-1">Next Audit Date</div>
              <div className="text-lg font-semibold text-gray-900">
                {new Date(posture.next_audit_date).toLocaleDateString()}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Compliance by Standard */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Compliance by Standard
          {onFilterByStandard && (
            <span className="text-sm font-normal text-gray-500 ml-2">(Click to filter)</span>
          )}
        </h3>
        <div className="space-y-3">
          {standardOrder.map((standard) => {
            const standardScore = posture.by_standard[standard];
            if (!standardScore) return null;

            return (
              <button
                key={standard}
                onClick={() => onFilterByStandard?.(standard)}
                disabled={!onFilterByStandard}
                className={`flex items-center w-full ${
                  onFilterByStandard
                    ? 'hover:bg-gray-50 cursor-pointer rounded-lg p-3 -mx-3 transition-colors'
                    : 'p-3'
                }`}
              >
                <div className="w-32 text-sm font-medium text-gray-700 text-left">
                  {standard.replace('_', '-')}
                </div>
                <div className="flex-1 mx-4">
                  <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
                    <div
                      className={`h-full ${getStandardBarColor(standardScore.score)} transition-all duration-300`}
                      style={{ width: `${standardScore.score}%` }}
                    />
                  </div>
                </div>
                <div className="w-32 text-right">
                  <span className="text-sm font-semibold text-gray-900">
                    Score: {standardScore.score}
                  </span>
                  <div className="text-xs text-gray-500">
                    {standardScore.violations} violation{standardScore.violations !== 1 ? 's' : ''}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Violations by Severity */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Violations by Severity
          {onFilterBySeverity && (
            <span className="text-sm font-normal text-gray-500 ml-2">(Click to filter)</span>
          )}
        </h3>
        <div className="space-y-3">
          {severityOrder.map((severity) => {
            const count = posture.by_severity[severity] || 0;
            const percentage =
              posture.total_violations > 0
                ? (count / posture.total_violations) * 100
                : 0;

            return (
              <button
                key={severity}
                onClick={() => onFilterBySeverity?.(severity)}
                disabled={!onFilterBySeverity || count === 0}
                className={`flex items-center w-full ${
                  onFilterBySeverity && count > 0
                    ? 'hover:bg-gray-50 cursor-pointer rounded-lg p-2 -mx-2 transition-colors'
                    : ''
                } ${count === 0 ? 'opacity-50' : ''}`}
              >
                <div className="w-32 text-sm font-medium text-gray-700 capitalize text-left">
                  {severity}
                </div>
                <div className="flex-1 mx-4">
                  <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
                    <div
                      className={`h-full ${getSeverityBarColor(severity)} transition-all duration-300`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
                <div className="w-20 text-right">
                  <span className="text-sm font-semibold text-gray-900">{count}</span>
                  <span className="text-xs text-gray-500 ml-1">
                    ({percentage.toFixed(0)}%)
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Violations by Status */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Violations by Status
          {onFilterByStatus && (
            <span className="text-sm font-normal text-gray-500 ml-2">(Click to filter)</span>
          )}
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(posture.by_status).map(([status, count]) => (
            <button
              key={status}
              onClick={() => onFilterByStatus?.(status as ComplianceStatus)}
              disabled={!onFilterByStatus || count === 0}
              className={`p-4 bg-gray-50 rounded-lg border border-gray-200 transition-all text-left ${
                onFilterByStatus && count > 0
                  ? 'hover:shadow-md hover:bg-gray-100 cursor-pointer'
                  : ''
              } ${count === 0 ? 'opacity-50' : ''}`}
            >
              <div className="text-sm font-medium text-gray-600 mb-1 capitalize">
                {status.replace('_', ' ')}
              </div>
              <div className="text-2xl font-bold text-gray-900">{count}</div>
              {onFilterByStatus && count > 0 && (
                <div className="text-xs text-blue-600 mt-2">Click to filter →</div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Compliance Trends */}
      {posture.compliance_trends && posture.compliance_trends.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Compliance Trends</h3>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="space-y-2">
              {posture.compliance_trends.slice(-7).map((trend, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    {new Date(trend.date).toLocaleDateString()}
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-sm font-medium text-gray-900">
                      Score: {trend.score}
                    </div>
                    <div className="text-sm text-gray-600">
                      {trend.violations} violation{trend.violations !== 1 ? 's' : ''}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Standard Details */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Standard Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {standardOrder.map((standard) => {
            const standardScore = posture.by_standard[standard];
            if (!standardScore) return null;

            return (
              <div
                key={standard}
                className="p-4 bg-gray-50 rounded-lg border border-gray-200"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="text-md font-semibold text-gray-900">
                      {standard.replace('_', '-')}
                    </h4>
                    <div className="text-xs text-gray-500 mt-1">
                      Last assessed: {new Date(standardScore.last_assessed).toLocaleDateString()}
                    </div>
                  </div>
                  <div className={`text-2xl font-bold ${getComplianceScoreColor(standardScore.score)}`}>
                    {standardScore.score}
                  </div>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Violations:</span>
                    <span className="font-medium text-gray-900">{standardScore.violations}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Compliant Controls:</span>
                    <span className="font-medium text-gray-900">
                      {standardScore.compliant_controls} / {standardScore.total_controls}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        standardScore.violations > 0
                          ? standardScore.violations >= 10
                            ? 'bg-red-500'
                            : 'bg-orange-500'
                          : 'bg-green-500'
                      }`}
                      style={{
                        width: `${(standardScore.compliant_controls / standardScore.total_controls) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// Helper functions
function getSeverityBarColor(severity: ComplianceSeverity): string {
  const colors: Record<ComplianceSeverity, string> = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-blue-500',
  };
  return colors[severity] || 'bg-gray-400';
}

function getStandardBarColor(score: number): string {
  if (score >= 90) return 'bg-green-500';
  if (score >= 70) return 'bg-yellow-500';
  if (score >= 50) return 'bg-orange-500';
  return 'bg-red-500';
}

function getComplianceScoreColor(score: number): string {
  if (score >= 90) return 'text-green-600';
  if (score >= 70) return 'text-yellow-600';
  if (score >= 50) return 'text-orange-600';
  return 'text-red-600';
}

function getRiskLevelColor(riskLevel: string): string {
  const colors: Record<string, string> = {
    low: 'text-green-600',
    medium: 'text-yellow-600',
    high: 'text-orange-600',
    critical: 'text-red-600',
  };
  return colors[riskLevel] || 'text-gray-600';
}

// Made with Bob