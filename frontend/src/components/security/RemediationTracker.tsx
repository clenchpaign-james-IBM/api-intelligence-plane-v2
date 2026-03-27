/**
 * Remediation Tracker Component
 * 
 * Tracks and displays remediation progress for vulnerabilities.
 */

import React from 'react';
import type { Vulnerability } from '../../types';
import { getStatusColor, formatRemediationTime } from '../../services/security';

interface RemediationTrackerProps {
  vulnerabilities: Vulnerability[];
}

export const RemediationTracker: React.FC<RemediationTrackerProps> = ({ vulnerabilities }) => {
  // Calculate remediation statistics
  const stats = calculateRemediationStats(vulnerabilities);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Remediation Tracker</h2>

      {/* Progress Overview */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm font-semibold text-gray-900">
            {stats.remediatedCount} / {stats.totalCount} ({stats.remediationRate.toFixed(1)}%)
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
          <div
            className="h-full bg-green-500 transition-all duration-300"
            style={{ width: `${stats.remediationRate}%` }}
          />
        </div>
      </div>

      {/* Status Breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="p-4 bg-red-50 rounded-lg border border-red-200">
          <div className="text-sm font-medium text-red-700 mb-1">Open</div>
          <div className="text-3xl font-bold text-red-900">{stats.openCount}</div>
        </div>

        <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <div className="text-sm font-medium text-yellow-700 mb-1">In Progress</div>
          <div className="text-3xl font-bold text-yellow-900">{stats.inProgressCount}</div>
        </div>

        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="text-sm font-medium text-green-700 mb-1">Remediated</div>
          <div className="text-3xl font-bold text-green-900">{stats.remediatedCount}</div>
        </div>

        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-sm font-medium text-blue-700 mb-1">Verified</div>
          <div className="text-3xl font-bold text-blue-900">{stats.verifiedCount}</div>
        </div>
      </div>

      {/* Recent Remediations */}
      {stats.recentRemediations.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Remediations</h3>
          <div className="space-y-3">
            {stats.recentRemediations.map((vuln) => (
              <div
                key={vuln.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
              >
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{vuln.title}</div>
                  <div className="text-sm text-gray-600 mt-1">
                    Remediated: {new Date(vuln.resolved_at!).toLocaleString()}
                  </div>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                    vuln.status
                  )}`}
                >
                  {vuln.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pending Remediations */}
      {stats.pendingRemediations.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Pending Remediations ({stats.pendingRemediations.length})
          </h3>
          <div className="space-y-3">
            {stats.pendingRemediations.slice(0, 5).map((vuln) => (
              <div
                key={vuln.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
              >
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{vuln.title}</div>
                  <div className="text-sm text-gray-600 mt-1">
                    Detected: {new Date(vuln.detected_at).toLocaleString()}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                      vuln.status
                    )}`}
                  >
                    {vuln.status.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className="text-sm text-gray-500">
                    {calculateAge(vuln.detected_at)}
                  </span>
                </div>
              </div>
            ))}
            {stats.pendingRemediations.length > 5 && (
              <div className="text-center text-sm text-gray-500 pt-2">
                + {stats.pendingRemediations.length - 5} more pending
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {vulnerabilities.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-2">
            <svg
              className="mx-auto h-12 w-12"
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
          </div>
          <p className="text-gray-500">No vulnerabilities to track</p>
        </div>
      )}
    </div>
  );
};

// Helper functions
interface RemediationStats {
  totalCount: number;
  openCount: number;
  inProgressCount: number;
  remediatedCount: number;
  verifiedCount: number;
  remediationRate: number;
  recentRemediations: Vulnerability[];
  pendingRemediations: Vulnerability[];
}

function calculateRemediationStats(vulnerabilities: Vulnerability[]): RemediationStats {
  const totalCount = vulnerabilities.length;
  const openCount = vulnerabilities.filter((v) => v.status === 'open').length;
  const inProgressCount = vulnerabilities.filter((v) => v.status === 'in_progress').length;
  const remediatedCount = vulnerabilities.filter((v) => v.status === 'remediated').length;
  const verifiedCount = vulnerabilities.filter((v) => v.status === 'verified').length;
  
  const remediationRate = totalCount > 0 
    ? ((remediatedCount + verifiedCount) / totalCount) * 100 
    : 0;

  // Recent remediations (last 10, sorted by resolved_at)
  const recentRemediations = vulnerabilities
    .filter((v) => v.resolved_at && (v.status === 'remediated' || v.status === 'verified'))
    .sort((a, b) => new Date(b.resolved_at!).getTime() - new Date(a.resolved_at!).getTime())
    .slice(0, 10);

  // Pending remediations (open or in_progress, sorted by severity then age)
  const pendingRemediations = vulnerabilities
    .filter((v) => v.status === 'open' || v.status === 'in_progress')
    .sort((a, b) => {
      // Sort by severity first
      const severityOrder = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
      const severityDiff = severityOrder[a.severity] - severityOrder[b.severity];
      if (severityDiff !== 0) return severityDiff;
      
      // Then by age (oldest first)
      return new Date(a.detected_at).getTime() - new Date(b.detected_at).getTime();
    });

  return {
    totalCount,
    openCount,
    inProgressCount,
    remediatedCount,
    verifiedCount,
    remediationRate,
    recentRemediations,
    pendingRemediations,
  };
}

function calculateAge(detectedAt: string): string {
  const now = new Date();
  const detected = new Date(detectedAt);
  const diffMs = now.getTime() - detected.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor(diffMs / (1000 * 60));

  if (diffDays > 0) return `${diffDays}d ago`;
  if (diffHours > 0) return `${diffHours}h ago`;
  if (diffMinutes > 0) return `${diffMinutes}m ago`;
  return 'just now';
}

// Made with Bob
