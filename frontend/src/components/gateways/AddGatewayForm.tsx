import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X } from '../../utils/carbonIcons';
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
    connection_url: '',
    connection_type: 'rest_api' as ConnectionType,
    credential_type: 'api_key',
    api_key: '',
    username: '',
    password: '',
    token: '',
    capabilities: ['discovery', 'metrics'],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.connection_url.trim()) newErrors.connection_url = 'Connection URL is required';
    
    // Validate credentials based on type
    if (formData.credential_type === 'api_key' && !formData.api_key.trim()) {
      newErrors.api_key = 'API Key is required';
    } else if (formData.credential_type === 'basic' && (!formData.username.trim() || !formData.password.trim())) {
      newErrors.credentials = 'Username and password are required';
    } else if (formData.credential_type === 'bearer' && !formData.token.trim()) {
      newErrors.token = 'Bearer token is required';
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
                Connection URL *
              </label>
              <input
                type="url"
                value={formData.connection_url}
                onChange={(e) => handleChange('connection_url', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.connection_url ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="https://api.example.com"
              />
              {errors.connection_url && <p className="mt-1 text-sm text-red-600">{errors.connection_url}</p>}
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

          {/* Credentials */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Credentials</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Credential Type
              </label>
              <select
                value={formData.credential_type}
                onChange={(e) => handleChange('credential_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="api_key">API Key</option>
                <option value="basic">Basic Auth</option>
                <option value="bearer">Bearer Token</option>
              </select>
            </div>

            {formData.credential_type === 'api_key' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key *
                </label>
                <input
                  type="password"
                  value={formData.api_key}
                  onChange={(e) => handleChange('api_key', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.api_key ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter API key"
                />
                {errors.api_key && <p className="mt-1 text-sm text-red-600">{errors.api_key}</p>}
              </div>
            )}

            {formData.credential_type === 'basic' && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Username *
                  </label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => handleChange('username', e.target.value)}
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
                    value={formData.password}
                    onChange={(e) => handleChange('password', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Password"
                  />
                </div>
                {errors.credentials && <p className="col-span-2 text-sm text-red-600">{errors.credentials}</p>}
              </div>
            )}

            {formData.credential_type === 'bearer' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bearer Token *
                </label>
                <input
                  type="password"
                  value={formData.token}
                  onChange={(e) => handleChange('token', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.token ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter bearer token"
                />
                {errors.token && <p className="mt-1 text-sm text-red-600">{errors.token}</p>}
              </div>
            )}
          </div>

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
              onClick={onClose}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={createMutation.isPending}
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