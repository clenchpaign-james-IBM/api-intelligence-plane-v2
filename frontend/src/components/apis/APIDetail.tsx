import { Clock, Activity, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import Card from '../common/Card';
import type { API } from '../../types';

/**
 * API Detail Component
 * 
 * Displays detailed information about a specific API including:
 * - Basic information and metadata
 * - Endpoints and methods
 * - Current metrics and health status
 * - Authentication configuration
 */

interface APIDetailProps {
  api: API;
  onClose?: () => void;
}

const APIDetail = ({ api, onClose }: APIDetailProps) => {
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
            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold ${getHealthColor(api.health_score)}`}>
              {api.health_score.toFixed(0)}
            </div>
            <div>
              <p className="text-sm text-gray-600">Health Score</p>
              <p className="text-lg font-semibold text-gray-900">
                {api.health_score >= 80 ? 'Excellent' : api.health_score >= 50 ? 'Good' : 'Poor'}
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
                {api.discovery_method.replace('_', ' ')}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Shadow API Warning */}
      {api.is_shadow && (
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

      {/* Current Metrics */}
      <Card title="Current Metrics" subtitle="Latest performance measurements">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600">Response Time (P50)</p>
            <p className="text-2xl font-bold text-gray-900">
              {api.current_metrics.response_time_p50.toFixed(1)}ms
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Response Time (P95)</p>
            <p className="text-2xl font-bold text-gray-900">
              {api.current_metrics.response_time_p95.toFixed(1)}ms
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Response Time (P99)</p>
            <p className="text-2xl font-bold text-gray-900">
              {api.current_metrics.response_time_p99.toFixed(1)}ms
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Error Rate</p>
            <p className="text-2xl font-bold text-gray-900">
              {(api.current_metrics.error_rate * 100).toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Throughput</p>
            <p className="text-2xl font-bold text-gray-900">
              {api.current_metrics.throughput.toFixed(1)} req/s
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Availability</p>
            <p className="text-2xl font-bold text-gray-900">
              {api.current_metrics.availability.toFixed(2)}%
            </p>
          </div>
        </div>
        <div className="mt-4 text-xs text-gray-500">
          Last measured: {new Date(api.current_metrics.measured_at).toLocaleString()}
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
            <p className="text-gray-900">{new Date(api.discovered_at).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-gray-600">Last Seen At</p>
            <p className="text-gray-900">{new Date(api.last_seen_at).toLocaleString()}</p>
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