/**
 * Remediation Action Card Component
 * 
 * Displays individual remediation action details with status tracking.
 * Used within PredictionRemediationPanel to show each action in the remediation plan.
 */

import React from 'react';
import { CheckCircle, XCircle, Clock, AlertCircle, Undo2 } from 'lucide-react';
import type { PredictionRemediationAction } from '../../types';

interface RemediationActionCardProps {
  action: PredictionRemediationAction;
  onRollback?: (actionId: string) => void;
  isRollingBack?: boolean;
}

const getActionTypeLabel = (actionType: string): string => {
  const labels: Record<string, string> = {
    rate_limiting: 'Rate Limiting',
    throttling: 'Throttling',
    cache_config: 'Cache Configuration',
    validation_policy: 'Validation Policy',
  };
  return labels[actionType] || actionType;
};

const getActionTypeColor = (actionType: string): string => {
  const colors: Record<string, string> = {
    rate_limiting: 'bg-blue-100 text-blue-800 border-blue-300',
    throttling: 'bg-purple-100 text-purple-800 border-purple-300',
    cache_config: 'bg-green-100 text-green-800 border-green-300',
    validation_policy: 'bg-orange-100 text-orange-800 border-orange-300',
  };
  return colors[actionType] || 'bg-gray-100 text-gray-800 border-gray-300';
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    case 'failed':
      return <XCircle className="w-5 h-5 text-red-500" />;
    case 'in_progress':
      return <Clock className="w-5 h-5 text-yellow-500 animate-pulse" />;
    case 'rolled_back':
      return <Undo2 className="w-5 h-5 text-gray-500" />;
    case 'pending':
    default:
      return <AlertCircle className="w-5 h-5 text-gray-400" />;
  }
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800 border-green-300';
    case 'failed':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'in_progress':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'rolled_back':
      return 'bg-gray-100 text-gray-800 border-gray-300';
    case 'pending':
    default:
      return 'bg-blue-100 text-blue-800 border-blue-300';
  }
};

export const RemediationActionCard: React.FC<RemediationActionCardProps> = ({
  action,
  onRollback,
  isRollingBack = false,
}) => {
  const canRollback = action.status === 'completed' && action.rollback_config && onRollback;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {getStatusIcon(action.status)}
          <div>
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium border ${getActionTypeColor(
                  action.action_type
                )}`}
              >
                {getActionTypeLabel(action.action_type)}
              </span>
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                  action.status
                )}`}
              >
                {action.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <p className="text-xs text-gray-500 font-mono mt-1">
              ID: {action.action_id.slice(0, 8)}...
            </p>
          </div>
        </div>
        
        {/* Rollback Button */}
        {canRollback && (
          <button
            onClick={() => onRollback(action.action_id)}
            disabled={isRollingBack}
            className="flex items-center gap-1 px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Rollback this action"
          >
            <Undo2 className="w-4 h-4" />
            {isRollingBack ? 'Rolling back...' : 'Rollback'}
          </button>
        )}
      </div>

      {/* Description */}
      <p className="text-sm text-gray-700 mb-3">{action.description}</p>

      {/* Configuration Details */}
      {action.config && Object.keys(action.config).length > 0 && (
        <div className="bg-gray-50 rounded p-3 mb-3">
          <h5 className="text-xs font-semibold text-gray-700 mb-2">Configuration</h5>
          <div className="space-y-1">
            {Object.entries(action.config).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between text-xs">
                <span className="text-gray-600 font-medium">
                  {key.replace(/_/g, ' ')}:
                </span>
                <span className="text-gray-900 font-mono">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Applied Timestamp */}
      {action.applied_at && (
        <div className="text-xs text-gray-600">
          <span className="font-medium">Applied:</span>{' '}
          {new Date(action.applied_at).toLocaleString()}
        </div>
      )}

      {/* Gateway Policy ID */}
      {action.gateway_policy_id && (
        <div className="text-xs text-gray-600 mt-1">
          <span className="font-medium">Policy ID:</span>{' '}
          <span className="font-mono">{action.gateway_policy_id}</span>
        </div>
      )}

      {/* Error Message */}
      {action.error_message && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded">
          <p className="text-xs text-red-700">
            <span className="font-semibold">Error:</span> {action.error_message}
          </p>
        </div>
      )}
    </div>
  );
};

export default RemediationActionCard;

// Made with Bob