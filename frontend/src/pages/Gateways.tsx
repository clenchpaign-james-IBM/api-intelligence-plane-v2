import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Heading, Button, Tag } from '@carbon/react';
import { Server, CheckCircle, XCircle, Clock, RefreshCw, Plus } from '../utils/carbonIcons';
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

  // Get status tag type
  const getStatusTagType = (status: string): 'green' | 'gray' | 'red' | 'warm-gray' => {
    switch (status) {
      case 'connected': return 'green';
      case 'disconnected': return 'gray';
      case 'error': return 'red';
      case 'maintenance': return 'warm-gray';
      default: return 'gray';
    }
  };

  // Get vendor tag type
  const getVendorTagType = (vendor: string): 'blue' | 'purple' | 'magenta' | 'cyan' | 'gray' => {
    switch (vendor) {
      case 'native': return 'blue';
      case 'kong': return 'purple';
      case 'apigee': return 'magenta';
      case 'aws': return 'cyan';
      case 'azure': return 'cyan';
      default: return 'gray';
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div style={{ padding: 'var(--cds-spacing-06)' }}>
        <Loading message="Loading gateways..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{ padding: 'var(--cds-spacing-06)' }}>
        <Error
          message="Failed to load gateways"
          details={error as Error}
        />
      </div>
    );
  }

  const gateways = data?.items || [];

  return (
    <div style={{ padding: 'var(--cds-spacing-06)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--cds-spacing-07)' }}>
        <div>
          <Heading style={{ marginBottom: 'var(--cds-spacing-03)' }}>API Gateways</Heading>
          <p style={{ color: 'var(--cds-text-secondary)', fontSize: '0.875rem' }}>
            Manage and monitor connected API gateways
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--cds-spacing-04)' }}>
          <Button
            kind="primary"
            renderIcon={Plus}
            onClick={() => setShowAddForm(true)}
          >
            Add Gateway
          </Button>
          <Button
            kind="secondary"
            renderIcon={RefreshCw}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--cds-spacing-05)', marginBottom: 'var(--cds-spacing-07)' }}>
        <Card padding="md">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
            <Server style={{ width: '40px', height: '40px' }} />
            <div>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Total Gateways</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>{gateways.length}</p>
            </div>
          </div>
        </Card>

        <Card padding="md">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
            <CheckCircle style={{ width: '40px', height: '40px', color: 'var(--cds-support-success)' }} />
            <div>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Connected</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {gateways.filter((g: Gateway) => g.status === 'connected').length}
              </p>
            </div>
          </div>
        </Card>

        <Card padding="md">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
            <Clock style={{ width: '40px', height: '40px', color: 'var(--cds-icon-secondary)' }} />
            <div>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Disconnected</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {gateways.filter((g: Gateway) => g.status === 'disconnected').length}
              </p>
            </div>
          </div>
        </Card>

        <Card padding="md">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
            <XCircle style={{ width: '40px', height: '40px', color: 'var(--cds-support-error)' }} />
            <div>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Error</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {gateways.filter((g: Gateway) => g.status === 'error').length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Gateway List */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 'var(--cds-spacing-06)' }}>
        {gateways.length === 0 ? (
          <div style={{ gridColumn: '1 / -1' }}>
            <Card padding="lg">
              <div style={{ textAlign: 'center', padding: 'var(--cds-spacing-09) 0' }}>
                <Server style={{ width: '64px', height: '64px', color: 'var(--cds-icon-secondary)', margin: '0 auto var(--cds-spacing-05)' }} />
                <h3 style={{ fontSize: '1.125rem', fontWeight: 500, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-03)' }}>No Gateways Configured</h3>
                <p style={{ color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-06)' }}>
                  Add your first API gateway to start discovering and monitoring APIs
                </p>
                <Button kind="primary" onClick={() => setShowAddForm(true)}>
                  Add Gateway
                </Button>
              </div>
            </Card>
          </div>
        ) : (
          gateways.map((gateway: Gateway) => (
            <Card key={gateway.id} padding="md">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-05)' }}>
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
                    {getStatusIcon(gateway.status)}
                    <div>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>{gateway.name}</h3>
                      <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>{gateway.connection_url}</p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-03)' }}>
                    <Tag type={getStatusTagType(gateway.status)}>
                      {gateway.status}
                    </Tag>
                    <Tag type={getVendorTagType(gateway.vendor)}>
                      {gateway.vendor}
                    </Tag>
                  </div>
                </div>

                {/* Capabilities */}
                {gateway.capabilities && gateway.capabilities.length > 0 && (
                  <div>
                    <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-03)' }}>Capabilities</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--cds-spacing-03)' }}>
                      {gateway.capabilities.map((capability) => (
                        <Tag key={capability} type="gray" size="sm">
                          {capability}
                        </Tag>
                      ))}
                    </div>
                  </div>
                )}

                {/* Metadata */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--cds-spacing-05)', fontSize: '0.875rem' }}>
                  <div>
                    <p style={{ color: 'var(--cds-text-secondary)' }}>Created</p>
                    <p style={{ fontWeight: 500, color: 'var(--cds-text-primary)' }}>
                      {new Date(gateway.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  {gateway.last_connected_at && (
                    <div>
                      <p style={{ color: 'var(--cds-text-secondary)' }}>Last Connected</p>
                      <p style={{ fontWeight: 500, color: 'var(--cds-text-primary)' }}>
                        {new Date(gateway.last_connected_at).toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: 'var(--cds-spacing-03)', paddingTop: 'var(--cds-spacing-05)', borderTop: '1px solid var(--cds-border-subtle)' }}>
                  <Button
                    kind="primary"
                    size="sm"
                    onClick={() => handleSync(gateway.id)}
                    disabled={syncingGateway === gateway.id}
                    style={{ flex: 1 }}
                  >
                    {syncingGateway === gateway.id ? 'Syncing...' : 'Sync Now'}
                  </Button>
                  <Button
                    kind="secondary"
                    size="sm"
                    onClick={() => handleViewDetails(gateway)}
                    style={{ flex: 1 }}
                  >
                    View Details
                  </Button>
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