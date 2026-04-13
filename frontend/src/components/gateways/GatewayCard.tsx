import React from 'react';
import { Server, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import Card from '../common/Card';
import type { Gateway } from '../../types';

/**
 * Gateway Card Component
 * 
 * Displays detailed gateway information in a card format.
 * Used in the Gateways page detail view to show comprehensive gateway details.
 * 
 * Features:
 * - Status indicator with icon
 * - Vendor badge
 * - Connection details
 * - Capabilities list
 * - Feature flags (metrics, security, rate limiting)
 * - Metadata (version, API count, last connected)
 */

interface GatewayCardProps {
  gateway: Gateway;
  onSync?: (gatewayId: string) => void;
  isSyncing?: boolean;
}

const GatewayCard: React.FC<GatewayCardProps> = ({ 
  gateway, 
  onSync,
  isSyncing = false 
}) => {
  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'disconnected':
        return <Clock className="w-5 h-5 text-gray-600" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'maintenance':
        return <Server className="w-5 h-5 text-yellow-600" />;
      default:
        return <Server className="w-5 h-5 text-gray-600" />;
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-green-100 text-green-800';
      case 'disconnected':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'maintenance':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Get vendor badge color
  const getVendorColor = (vendor: string) => {
    switch (vendor) {
      case 'native':
        return 'bg-blue-100 text-blue-800';
      case 'webmethods':
        return 'bg-green-100 text-green-800';
      case 'kong':
        return 'bg-purple-100 text-purple-800';
      case 'apigee':
        return 'bg-orange-100 text-orange-800';
      case 'aws':
        return 'bg-yellow-100 text-yellow-800';
      case 'azure':
        return 'bg-cyan-100 text-cyan-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card title={gateway.name} subtitle={`${gateway.vendor} Gateway`}>
      <div className="space-y-6">
        {/* Status and Basic Info */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm font-medium text-gray-600">Status</p>
            <div className="mt-1 flex items-center gap-2">
              {getStatusIcon(gateway.status)}
              <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(gateway.status)}`}>
                {gateway.status}
              </span>
            </div>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Vendor</p>
            <p className="mt-1">
              <span className={`px-2 py-1 text-xs font-medium rounded ${getVendorColor(gateway.vendor)}`}>
                {gateway.vendor}
              </span>
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Base URL</p>
            <p className="mt-1 text-sm text-gray-900 break-all">{gateway.base_url}</p>
          </div>
          {gateway.transactional_logs_url && (
            <div>
              <p className="text-sm font-medium text-gray-600">Transactional Logs URL</p>
              <p className="mt-1 text-sm text-gray-900 break-all">{gateway.transactional_logs_url}</p>
            </div>
          )}
          <div>
            <p className="text-sm font-medium text-gray-600">Connection Type</p>
            <p className="mt-1 text-sm text-gray-900">{gateway.connection_type}</p>
          </div>
          {gateway.base_url_credentials && (
            <div>
              <p className="text-sm font-medium text-gray-600">Base URL Authentication</p>
              <p className="mt-1 text-sm text-gray-900">{gateway.base_url_credentials.type}</p>
            </div>
          )}
          {gateway.transactional_logs_credentials && (
            <div>
              <p className="text-sm font-medium text-gray-600">Logs Authentication</p>
              <p className="mt-1 text-sm text-gray-900">{gateway.transactional_logs_credentials.type}</p>
            </div>
          )}
          <div>
            <p className="text-sm font-medium text-gray-600">API Count</p>
            <p className="mt-1 text-sm text-gray-900">{gateway.api_count}</p>
          </div>
          {gateway.version && (
            <div>
              <p className="text-sm font-medium text-gray-600">Version</p>
              <p className="mt-1 text-sm text-gray-900">{gateway.version}</p>
            </div>
          )}
          {gateway.last_connected_at && (
            <div>
              <p className="text-sm font-medium text-gray-600">Last Connected</p>
              <p className="mt-1 text-sm text-gray-900">
                {new Date(gateway.last_connected_at).toLocaleString()}
              </p>
            </div>
          )}
          <div>
            <p className="text-sm font-medium text-gray-600">Created</p>
            <p className="mt-1 text-sm text-gray-900">
              {new Date(gateway.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Error Message (if any) */}
        {gateway.last_error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800">Last Error</p>
                <p className="text-sm text-red-700 mt-1">{gateway.last_error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Capabilities */}
        {gateway.capabilities && gateway.capabilities.length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-600 mb-2">Capabilities</p>
            <div className="flex flex-wrap gap-2">
              {gateway.capabilities.map((cap, idx) => (
                <span 
                  key={idx} 
                  className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded"
                >
                  {cap}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Features */}
        <div>
          <p className="text-sm font-medium text-gray-600 mb-2">Features</p>
          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center gap-2">
              {gateway.metrics_enabled ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <XCircle className="w-4 h-4 text-gray-400" />
              )}
              <span className="text-sm text-gray-900">Metrics</span>
            </div>
            <div className="flex items-center gap-2">
              {gateway.security_scanning_enabled ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <XCircle className="w-4 h-4 text-gray-400" />
              )}
              <span className="text-sm text-gray-900">Security Scanning</span>
            </div>
            <div className="flex items-center gap-2">
              {gateway.rate_limiting_enabled ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <XCircle className="w-4 h-4 text-gray-400" />
              )}
              <span className="text-sm text-gray-900">Rate Limiting</span>
            </div>
          </div>
        </div>

        {/* Configuration (if any) */}
        {gateway.configuration && Object.keys(gateway.configuration).length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-600 mb-2">Configuration</p>
            <div className="bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto">
              <pre className="text-xs text-gray-800 whitespace-pre-wrap">
                {JSON.stringify(gateway.configuration, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Metadata (if any) */}
        {gateway.metadata && Object.keys(gateway.metadata).length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-600 mb-2">Metadata</p>
            <div className="bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto">
              <pre className="text-xs text-gray-800 whitespace-pre-wrap">
                {JSON.stringify(gateway.metadata, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Actions */}
        {onSync && (
          <div className="flex gap-3 pt-4 border-t">
            <button
              onClick={() => onSync(gateway.id)}
              disabled={isSyncing}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSyncing ? 'Syncing...' : 'Sync Now'}
            </button>
          </div>
        )}
      </div>
    </Card>
  );
};

export default GatewayCard;

// Made with Bob