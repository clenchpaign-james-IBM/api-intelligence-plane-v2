import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Server, CheckCircle, XCircle, Clock, RefreshCw, Plus } from 'lucide-react';
import Card from '../components/common/Card';
import Loading from '../components/common/Loading';
import Error from '../components/common/Error';
import AddGatewayForm from '../components/gateways/AddGatewayForm';
import { api } from '../services/api';
import type { Gateway } from '../types';

/**
 * Gateways Page
 * 
 * Page for managing API gateways:
 * - List of connected gateways
 * - Gateway status and capabilities
 * - Sync and management actions
 */
const Gateways = () => {
  const queryClient = useQueryClient();
  const [selectedGateway, setSelectedGateway] = useState<Gateway | null>(null);
  const [syncingGateway, setSyncingGateway] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  // Fetch gateways
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['gateways'],
    queryFn: () => api.gateways.list(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Sync gateway mutation
  const syncMutation = useMutation({
    mutationFn: (gatewayId: string) => api.gateways.sync(gatewayId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gateways'] });
      setSyncingGateway(null);
    },
    onError: (error: Error) => {
      console.error('Sync failed:', error);
      setSyncingGateway(null);
      alert('Failed to sync gateway. Please try again.');
    },
  });

  // Handle sync
  const handleSync = (gatewayId: string) => {
    setSyncingGateway(gatewayId);
    syncMutation.mutate(gatewayId);
  };

  // Handle view details
  const handleViewDetails = (gateway: Gateway) => {
    setSelectedGateway(gateway);
    // TODO: Implement gateway details modal or navigate to details page
    alert(`Gateway Details:\n\nName: ${gateway.name}\nVendor: ${gateway.vendor}\nStatus: ${gateway.status}\nURL: ${gateway.connection_url}`);
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'disconnected': return <Clock className="w-5 h-5 text-gray-600" />;
      case 'error': return <XCircle className="w-5 h-5 text-red-600" />;
      case 'maintenance': return <Server className="w-5 h-5 text-yellow-600" />;
      default: return <Server className="w-5 h-5 text-gray-600" />;
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'bg-green-100 text-green-800';
      case 'disconnected': return 'bg-gray-100 text-gray-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'maintenance': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Get vendor badge color
  const getVendorColor = (vendor: string) => {
    switch (vendor) {
      case 'native': return 'bg-blue-100 text-blue-800';
      case 'kong': return 'bg-purple-100 text-purple-800';
      case 'apigee': return 'bg-orange-100 text-orange-800';
      case 'aws': return 'bg-yellow-100 text-yellow-800';
      case 'azure': return 'bg-cyan-100 text-cyan-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="p-6">
        <Loading message="Loading gateways..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-6">
        <Error
          message="Failed to load gateways"
          details={error as Error}
        />
      </div>
    );
  }

  const gateways = data?.items || [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">API Gateways</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage and monitor connected API gateways
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowAddForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Gateway
          </button>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card padding="md">
          <div className="flex items-center gap-3">
            <Server className="w-10 h-10 text-blue-600" />
            <div>
              <p className="text-sm text-gray-600">Total Gateways</p>
              <p className="text-2xl font-bold text-gray-900">{gateways.length}</p>
            </div>
          </div>
        </Card>

        <Card padding="md">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-10 h-10 text-green-600" />
            <div>
              <p className="text-sm text-gray-600">Connected</p>
              <p className="text-2xl font-bold text-gray-900">
                {gateways.filter((g: Gateway) => g.status === 'connected').length}
              </p>
            </div>
          </div>
        </Card>

        <Card padding="md">
          <div className="flex items-center gap-3">
            <Clock className="w-10 h-10 text-gray-600" />
            <div>
              <p className="text-sm text-gray-600">Disconnected</p>
              <p className="text-2xl font-bold text-gray-900">
                {gateways.filter((g: Gateway) => g.status === 'disconnected').length}
              </p>
            </div>
          </div>
        </Card>

        <Card padding="md">
          <div className="flex items-center gap-3">
            <XCircle className="w-10 h-10 text-red-600" />
            <div>
              <p className="text-sm text-gray-600">Error</p>
              <p className="text-2xl font-bold text-gray-900">
                {gateways.filter((g: Gateway) => g.status === 'error').length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Gateway List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {gateways.length === 0 ? (
          <div className="col-span-full">
            <Card padding="lg">
              <div className="text-center py-12">
                <Server className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Gateways Configured</h3>
                <p className="text-gray-600 mb-6">
                  Add your first API gateway to start discovering and monitoring APIs
                </p>
                <button
                  onClick={() => setShowAddForm(true)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Add Gateway
                </button>
              </div>
            </Card>
          </div>
        ) : (
          gateways.map((gateway: Gateway) => (
            <Card key={gateway.id} padding="md">
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(gateway.status)}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{gateway.name}</h3>
                      <p className="text-sm text-gray-600">{gateway.connection_url}</p>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(gateway.status)}`}>
                      {gateway.status}
                    </span>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getVendorColor(gateway.vendor)}`}>
                      {gateway.vendor}
                    </span>
                  </div>
                </div>

                {/* Capabilities */}
                {gateway.capabilities && gateway.capabilities.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">Capabilities</p>
                    <div className="flex flex-wrap gap-2">
                      {gateway.capabilities.map((capability) => (
                        <span
                          key={capability}
                          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                        >
                          {capability}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Metadata */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Created</p>
                    <p className="font-medium text-gray-900">
                      {new Date(gateway.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  {gateway.last_connected_at && (
                    <div>
                      <p className="text-gray-600">Last Connected</p>
                      <p className="font-medium text-gray-900">
                        {new Date(gateway.last_connected_at).toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-4 border-t border-gray-200 justify-end">
                  <button
                    onClick={() => handleSync(gateway.id)}
                    disabled={syncingGateway === gateway.id}
                    className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                  >
                    {syncingGateway === gateway.id ? 'Syncing...' : 'Sync Now'}
                  </button>
                  <button
                    onClick={() => handleViewDetails(gateway)}
                    className="px-3 py-1 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors text-xs flex items-center gap-1"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Add Gateway Modal */}
      {showAddForm && (
        <AddGatewayForm
          onClose={() => setShowAddForm(false)}
          onSuccess={() => {
            setShowAddForm(false);
            refetch();
          }}
        />
      )}
    </div>
  );
};

export default Gateways;

// Made with Bob