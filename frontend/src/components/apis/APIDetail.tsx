import { Clock, Activity, AlertTriangle, CheckCircle, XCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import Card from '../common/Card';
import PolicyActionsViewer from './PolicyActionsViewer';
import APIDefinitionViewer from './APIDefinitionViewer';
import type { API } from '../../types';

/**
 * API Detail Component
 * 
 * Displays detailed information about a specific API including:
 * - Basic information and metadata
 * - Endpoints and methods
 * - Intelligence metadata and health status
 * - Authentication configuration
 */

interface APIDetailProps {
  api: API;
  onClose?: () => void;
}

const APIDetail = ({ api, onClose }: APIDetailProps) => {
  const [showVendorMetadata, setShowVendorMetadata] = useState(false);

  // Get health score color
  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 50) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'inactive': return <Clock className="w-5 h-5 text-gray-600" />;
      case 'deprecated': return <AlertTriangle className="w-5 h-5 text-orange-600" />;
      case 'failed': return <XCircle className="w-5 h-5 text-red-600" />;
      default: return <Activity className="w-5 h-5 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-2xl font-bold text-gray-900">{api.name}</h2>
            {api.version && (
              <span className="px-3 py-1 text-sm font-medium bg-gray-100 text-gray-700 rounded">
                v{api.version}
              </span>
            )}
          </div>
          <p className="text-gray-600">{api.base_path}</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XCircle className="w-6 h-6" />
          </button>
        )}
      </div>

      {/* Status and Health */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card padding="md">
          <div className="flex items-center gap-3">
            {getStatusIcon(api.status)}
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <p className="text-lg font-semibold text-gray-900 capitalize">{api.status}</p>
            </div>
          </div>
        </Card>

        <Card padding="md">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold ${getHealthColor(api.intelligence_metadata?.health_score ?? 0)}`}>
              {(api.intelligence_metadata?.health_score ?? 0).toFixed(0)}
            </div>
            <div>
              <p className="text-sm text-gray-600">Health Score</p>
              <p className="text-lg font-semibold text-gray-900">
                {(api.intelligence_metadata?.health_score ?? 0) >= 80
                  ? 'Excellent'
                  : (api.intelligence_metadata?.health_score ?? 0) >= 50
                    ? 'Good'
                    : 'Poor'}
              </p>
            </div>
          </div>
        </Card>

        <Card padding="md">
          <div className="flex items-center gap-3">
            <Activity className="w-12 h-12 text-blue-600" />
            <div>
              <p className="text-sm text-gray-600">Discovery Method</p>
              <p className="text-lg font-semibold text-gray-900 capitalize">
                {(api.intelligence_metadata?.discovery_method || 'registered').replace('_', ' ')}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Shadow API Warning */}
      {api.intelligence_metadata?.is_shadow && (
        <div className="p-4 bg-orange-50 border-l-4 border-orange-500 rounded">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            <p className="font-medium text-orange-900">Shadow API Detected</p>
          </div>
          <p className="text-sm text-orange-700 mt-1">
            This API was discovered through traffic analysis and may not be officially documented.
          </p>
        </div>
      )}

      {/* Intelligence Metadata */}
      <Card title="Intelligence Metadata" subtitle="AI-derived discovery and risk insights">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Risk Score</p>
            <p className="text-2xl font-bold text-gray-900">
              {(api.intelligence_metadata?.risk_score ?? 0).toFixed(0)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Security Score</p>
            <p className="text-2xl font-bold text-gray-900">
              {(api.intelligence_metadata?.security_score ?? 0).toFixed(0)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Shadow API</p>
            <p className="text-2xl font-bold text-gray-900">
              {api.intelligence_metadata?.is_shadow ? 'Yes' : 'No'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Usage Trend</p>
            <p className="text-sm font-semibold text-gray-900 capitalize">
              {api.intelligence_metadata?.usage_trend?.replace('_', ' ') || 'Not available'}
            </p>
          </div>
        </div>
      </Card>

      {/* Endpoints */}
      <Card title="Endpoints" subtitle={`${api.endpoints.length} endpoints available`}>
        <div className="space-y-2">
          {api.endpoints.map((endpoint, index) => (
            <div
              key={index}
              className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className={`px-2 py-1 text-xs font-mono font-bold rounded ${
                  endpoint.method === 'GET' ? 'bg-blue-100 text-blue-800' :
                  endpoint.method === 'POST' ? 'bg-green-100 text-green-800' :
                  endpoint.method === 'PUT' ? 'bg-yellow-100 text-yellow-800' :
                  endpoint.method === 'DELETE' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {endpoint.method}
                </span>
                <code className="text-sm font-mono text-gray-900">{endpoint.path}</code>
              </div>
              {endpoint.description && (
                <p className="text-sm text-gray-600 mt-1 ml-16">{endpoint.description}</p>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Authentication */}
      <Card title="Authentication" subtitle="Security configuration">
        <div className="space-y-3">
          <div>
            <p className="text-sm text-gray-600">Type</p>
            <p className="text-lg font-semibold text-gray-900 capitalize">
              {api.authentication_type.replace('_', ' ')}
            </p>
          </div>
          {api.authentication_config && Object.keys(api.authentication_config).length > 0 && (
            <div>
              <p className="text-sm text-gray-600 mb-2">Configuration</p>
              <div className="p-3 bg-gray-50 rounded font-mono text-sm">
                {Object.entries(api.authentication_config).map(([key, value]) => (
                  <div key={key} className="flex gap-2">
                    <span className="text-gray-600">{key}:</span>
                    <span className="text-gray-900">
                      {typeof value === 'string' && value.length > 50 ? '***' : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Policy Actions */}
      <PolicyActionsViewer policyActions={api.policy_actions} />

      {/* API Definition */}
      {api.api_definition && (
        <APIDefinitionViewer apiDefinition={api.api_definition} />
      )}

      {/* Vendor Metadata (Collapsible) */}
      {api.vendor_metadata && Object.keys(api.vendor_metadata).length > 0 && (
        <Card title="Vendor Metadata" subtitle="Gateway-specific configuration and data">
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <button
              onClick={() => setShowVendorMetadata(!showVendorMetadata)}
              className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <span className="font-medium text-gray-900">
                {Object.keys(api.vendor_metadata).length} vendor-specific fields
              </span>
              {showVendorMetadata ? (
                <ChevronDown className="w-5 h-5 text-gray-600" />
              ) : (
                <ChevronRight className="w-5 h-5 text-gray-600" />
              )}
            </button>
            {showVendorMetadata && (
              <div className="p-4 bg-white">
                <pre className="text-sm text-gray-800 overflow-x-auto">
                  <code>{JSON.stringify(api.vendor_metadata, null, 2)}</code>
                </pre>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Tags */}
      {api.tags && api.tags.length > 0 && (
        <Card title="Tags" subtitle="API categorization">
          <div className="flex flex-wrap gap-2">
            {api.tags.map((tag) => (
              <span
                key={tag}
                className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium"
              >
                {tag}
              </span>
            ))}
          </div>
        </Card>
      )}

      {/* Metadata */}
      <Card title="Metadata" subtitle="Additional information">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-600">API ID</p>
            <p className="font-mono text-gray-900">{api.id}</p>
          </div>
          <div>
            <p className="text-gray-600">Gateway ID</p>
            <p className="font-mono text-gray-900">{api.gateway_id}</p>
          </div>
          <div>
            <p className="text-gray-600">Discovered At</p>
            <p className="text-gray-900">
              {new Date(api.intelligence_metadata.discovered_at).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-gray-600">Last Seen At</p>
            <p className="text-gray-900">
              {new Date(api.intelligence_metadata.last_seen_at).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-gray-600">Created At</p>
            <p className="text-gray-900">{new Date(api.created_at).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-gray-600">Updated At</p>
            <p className="text-gray-900">{new Date(api.updated_at).toLocaleString()}</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default APIDetail;

// Made with Bob