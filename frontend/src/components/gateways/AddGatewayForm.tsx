import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, CheckCircle, XCircle, Loader } from 'lucide-react';
import { api } from '../../services/api';
import Button from '../common/Button';
import Card from '../common/Card';
import type { GatewayVendor, ConnectionType } from '../../types';

interface AddGatewayFormProps {
  onClose: () => void;
  onSuccess?: () => void;
}

/**
 * AddGatewayForm Component
 * 
 * Form for adding a new API Gateway with validation
 */
const AddGatewayForm = ({ onClose, onSuccess }: AddGatewayFormProps) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    name: '',
    vendor: 'native' as GatewayVendor,
    version: '',
    base_url: '',
    transactional_logs_url: '',
    connection_type: 'rest_api' as ConnectionType,
    base_url_credential_type: 'none',
    base_url_api_key: '',
    base_url_username: '',
    base_url_password: '',
    base_url_token: '',
    transactional_logs_credential_type: 'none',
    transactional_logs_api_key: '',
    transactional_logs_username: '',
    transactional_logs_password: '',
    transactional_logs_token: '',
    capabilities: ['discovery', 'metrics'],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [connectionTest, setConnectionTest] = useState<{
    status: 'idle' | 'testing' | 'success' | 'error';
    message?: string;
    latency?: number;
  }>({ status: 'idle' });

  // Create gateway mutation
  const createMutation = useMutation({
    mutationFn: (data: any) => api.gateways.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gateways'] });
      onSuccess?.();
      onClose();
    },
    onError: (error: any) => {
      console.error('Failed to create gateway:', error);
      setErrors({ submit: error.message || 'Failed to create gateway' });
    },
  });

  // Test connection mutation
  const testConnectionMutation = useMutation({
    mutationFn: (data: any) => api.gateways.testConnection(data),
    onSuccess: (response: any) => {
      setConnectionTest({
        status: 'success',
        message: response.message || 'Connection successful',
        latency: response.latency_ms,
      });
    },
    onError: (error: any) => {
      setConnectionTest({
        status: 'error',
        message: error.response?.data?.detail || error.message || 'Connection failed',
      });
    },
  });

  const handleTestConnection = () => {
    // Validate required fields before testing
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.base_url.trim()) newErrors.base_url = 'Base URL is required';
    
    // Validate base URL credentials based on type
    if (formData.base_url_credential_type === 'api_key' && !formData.base_url_api_key.trim()) {
      newErrors.base_url_api_key = 'API Key is required for base URL';
    } else if (formData.base_url_credential_type === 'basic' && (!formData.base_url_username.trim() || !formData.base_url_password.trim())) {
      newErrors.base_url_credentials = 'Username and password are required for base URL';
    } else if (formData.base_url_credential_type === 'bearer' && !formData.base_url_token.trim()) {
      newErrors.base_url_token = 'Bearer token is required for base URL';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setConnectionTest({ status: 'testing' });
    testConnectionMutation.mutate(formData);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.base_url.trim()) newErrors.base_url = 'Base URL is required';
    
    // Validate base URL credentials based on type
    if (formData.base_url_credential_type === 'api_key' && !formData.base_url_api_key.trim()) {
      newErrors.base_url_api_key = 'API Key is required for base URL';
    } else if (formData.base_url_credential_type === 'basic' && (!formData.base_url_username.trim() || !formData.base_url_password.trim())) {
      newErrors.base_url_credentials = 'Username and password are required for base URL';
    } else if (formData.base_url_credential_type === 'bearer' && !formData.base_url_token.trim()) {
      newErrors.base_url_token = 'Bearer token is required for base URL';
    }
    
    // Validate transactional logs credentials if URL is provided
    if (formData.transactional_logs_url.trim()) {
      if (formData.transactional_logs_credential_type === 'api_key' && !formData.transactional_logs_api_key.trim()) {
        newErrors.transactional_logs_api_key = 'API Key is required for transactional logs';
      } else if (formData.transactional_logs_credential_type === 'basic' && (!formData.transactional_logs_username.trim() || !formData.transactional_logs_password.trim())) {
        newErrors.transactional_logs_credentials = 'Username and password are required for transactional logs';
      } else if (formData.transactional_logs_credential_type === 'bearer' && !formData.transactional_logs_token.trim()) {
        newErrors.transactional_logs_token = 'Bearer token is required for transactional logs';
      }
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    createMutation.mutate(formData);
  };

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Add New Gateway</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Gateway Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="My API Gateway"
              />
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Vendor *
                </label>
                <select
                  value={formData.vendor}
                  onChange={(e) => handleChange('vendor', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="native">Native</option>
                  <option value="webmethods">WebMethods</option>
                  <option value="kong">Kong</option>
                  <option value="apigee">Apigee</option>
                  <option value="aws">AWS API Gateway</option>
                  <option value="azure">Azure API Management</option>
                  <option value="custom">Custom</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Version
                </label>
                <input
                  type="text"
                  value={formData.version}
                  onChange={(e) => handleChange('version', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="1.0.0"
                />
              </div>
            </div>
          </div>

          {/* Connection Details */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Connection Details</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Base URL *
              </label>
              <input
                type="url"
                value={formData.base_url}
                onChange={(e) => handleChange('base_url', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.base_url ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="https://gateway.example.com:5555"
              />
              <p className="mt-1 text-xs text-gray-500">Primary endpoint for APIs, Policies, and PolicyActions</p>
              {errors.base_url && <p className="mt-1 text-sm text-red-600">{errors.base_url}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Transactional Logs URL (Optional)
              </label>
              <input
                type="url"
                value={formData.transactional_logs_url}
                onChange={(e) => handleChange('transactional_logs_url', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://analytics.example.com/logs"
              />
              <p className="mt-1 text-xs text-gray-500">Separate endpoint for analytics data (if different from base URL)</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Connection Type
              </label>
              <select
                value={formData.connection_type}
                onChange={(e) => handleChange('connection_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="rest_api">REST API</option>
                <option value="grpc">gRPC</option>
                <option value="graphql">GraphQL</option>
              </select>
            </div>
          </div>

          {/* Base URL Credentials */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Base URL Credentials</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Credential Type
              </label>
              <select
                value={formData.base_url_credential_type}
                onChange={(e) => handleChange('base_url_credential_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="none">No Authentication</option>
                <option value="api_key">API Key</option>
                <option value="basic">Basic Auth</option>
                <option value="bearer">Bearer Token</option>
              </select>
            </div>

            {formData.base_url_credential_type === 'api_key' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key *
                </label>
                <input
                  type="password"
                  value={formData.base_url_api_key}
                  onChange={(e) => handleChange('base_url_api_key', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.base_url_api_key ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter API key"
                />
                {errors.base_url_api_key && <p className="mt-1 text-sm text-red-600">{errors.base_url_api_key}</p>}
              </div>
            )}

            {formData.base_url_credential_type === 'basic' && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Username *
                  </label>
                  <input
                    type="text"
                    value={formData.base_url_username}
                    onChange={(e) => handleChange('base_url_username', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Username"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password *
                  </label>
                  <input
                    type="password"
                    value={formData.base_url_password}
                    onChange={(e) => handleChange('base_url_password', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Password"
                  />
                </div>
                {errors.base_url_credentials && <p className="col-span-2 text-sm text-red-600">{errors.base_url_credentials}</p>}
              </div>
            )}

            {formData.base_url_credential_type === 'bearer' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bearer Token *
                </label>
                <input
                  type="password"
                  value={formData.base_url_token}
                  onChange={(e) => handleChange('base_url_token', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.base_url_token ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter bearer token"
                />
                {errors.base_url_token && <p className="mt-1 text-sm text-red-600">{errors.base_url_token}</p>}
              </div>
            )}
          </div>

          {/* Transactional Logs Credentials */}
          {formData.transactional_logs_url && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Transactional Logs Credentials (Optional)</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Credential Type
                </label>
                <select
                  value={formData.transactional_logs_credential_type}
                  onChange={(e) => handleChange('transactional_logs_credential_type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="none">No Authentication</option>
                  <option value="api_key">API Key</option>
                  <option value="basic">Basic Auth</option>
                  <option value="bearer">Bearer Token</option>
                </select>
              </div>

              {formData.transactional_logs_credential_type === 'api_key' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    API Key *
                  </label>
                  <input
                    type="password"
                    value={formData.transactional_logs_api_key}
                    onChange={(e) => handleChange('transactional_logs_api_key', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                      errors.transactional_logs_api_key ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Enter API key"
                  />
                  {errors.transactional_logs_api_key && <p className="mt-1 text-sm text-red-600">{errors.transactional_logs_api_key}</p>}
                </div>
              )}

              {formData.transactional_logs_credential_type === 'basic' && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Username *
                    </label>
                    <input
                      type="text"
                      value={formData.transactional_logs_username}
                      onChange={(e) => handleChange('transactional_logs_username', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Username"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Password *
                    </label>
                    <input
                      type="password"
                      value={formData.transactional_logs_password}
                      onChange={(e) => handleChange('transactional_logs_password', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Password"
                    />
                  </div>
                  {errors.transactional_logs_credentials && <p className="col-span-2 text-sm text-red-600">{errors.transactional_logs_credentials}</p>}
                </div>
              )}

              {formData.transactional_logs_credential_type === 'bearer' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bearer Token *
                  </label>
                  <input
                    type="password"
                    value={formData.transactional_logs_token}
                    onChange={(e) => handleChange('transactional_logs_token', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                      errors.transactional_logs_token ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Enter bearer token"
                  />
                  {errors.transactional_logs_token && <p className="mt-1 text-sm text-red-600">{errors.transactional_logs_token}</p>}
                </div>
              )}
            </div>
          )}

          {/* Connection Test Status */}
          {connectionTest.status !== 'idle' && (
            <div className={`p-4 border rounded-lg ${
              connectionTest.status === 'success' ? 'bg-green-50 border-green-200' :
              connectionTest.status === 'error' ? 'bg-red-50 border-red-200' :
              'bg-blue-50 border-blue-200'
            }`}>
              <div className="flex items-center gap-2">
                {connectionTest.status === 'testing' && <Loader className="w-5 h-5 text-blue-600 animate-spin" />}
                {connectionTest.status === 'success' && <CheckCircle className="w-5 h-5 text-green-600" />}
                {connectionTest.status === 'error' && <XCircle className="w-5 h-5 text-red-600" />}
                <div className="flex-1">
                  <p className={`text-sm font-medium ${
                    connectionTest.status === 'success' ? 'text-green-800' :
                    connectionTest.status === 'error' ? 'text-red-800' :
                    'text-blue-800'
                  }`}>
                    {connectionTest.status === 'testing' ? 'Testing connection...' :
                     connectionTest.status === 'success' ? 'Connection successful!' :
                     'Connection failed'}
                  </p>
                  {connectionTest.message && (
                    <p className={`text-xs mt-1 ${
                      connectionTest.status === 'success' ? 'text-green-700' :
                      connectionTest.status === 'error' ? 'text-red-700' :
                      'text-blue-700'
                    }`}>
                      {connectionTest.message}
                    </p>
                  )}
                  {connectionTest.latency && (
                    <p className="text-xs mt-1 text-green-700">
                      Latency: {connectionTest.latency}ms
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Submit Error */}
          {errors.submit && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{errors.submit}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="secondary"
              onClick={handleTestConnection}
              disabled={testConnectionMutation.isPending}
              className="flex-1"
            >
              {testConnectionMutation.isPending ? 'Testing...' : 'Test Connection'}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={createMutation.isPending || connectionTest.status === 'testing'}
              className="flex-1"
            >
              {createMutation.isPending ? 'Adding...' : 'Add Gateway'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default AddGatewayForm;

// Made with Bob