import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Heading, Button } from '@carbon/react';
import { ArrowLeft } from '../utils/carbonIcons';
import APIList from '../components/apis/APIList';
import APIDetail from '../components/apis/APIDetail';
import Loading from '../components/common/Loading';
import Error from '../components/common/Error';
import { api } from '../services/api';
import type { API } from '../types';

/**
 * APIs Page
 * 
 * Main page for browsing and managing APIs:
 * - List view with search and filters
 * - Detail view for selected API
 * - Metrics visualization
 */
const APIs = () => {
  const [selectedAPI, setSelectedAPI] = useState<API | null>(null);

  // Fetch APIs
  const { data, isLoading, error } = useQuery({
    queryKey: ['apis'],
    queryFn: () => api.apis.list(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Handle API selection
  const handleSelectAPI = (api: API) => {
    setSelectedAPI(api);
  };

  // Handle back to list
  const handleBack = () => {
    setSelectedAPI(null);
  };

  // Loading state
  if (isLoading) {
    return (
      <div style={{ padding: 'var(--cds-spacing-06)' }}>
        <Loading message="Loading APIs..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{ padding: 'var(--cds-spacing-06)' }}>
        <Error
          message="Failed to load APIs"
          details={error as Error}
        />
      </div>
    );
  }

  const apis = data?.items || [];

  return (
    <div style={{ padding: 'var(--cds-spacing-06)' }}>
      {/* Header */}
      {!selectedAPI ? (
        <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
          <Heading style={{ marginBottom: 'var(--cds-spacing-03)' }}>API Inventory</Heading>
          <p style={{ color: 'var(--cds-text-secondary)', fontSize: '0.875rem' }}>
            Browse and manage all discovered APIs across your gateways
          </p>
        </div>
      ) : (
        <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
          <Button
            kind="ghost"
            renderIcon={ArrowLeft}
            onClick={handleBack}
            style={{ marginBottom: 'var(--cds-spacing-05)' }}
          >
            Back to API List
          </Button>
        </div>
      )}

      {/* Content */}
      {!selectedAPI ? (
        <APIList
          apis={apis}
          onSelectAPI={handleSelectAPI}
          loading={isLoading}
        />
      ) : (
        <APIDetail
          api={selectedAPI}
          onClose={handleBack}
        />
      )}
    </div>
  );
};

export default APIs;

// Made with Bob