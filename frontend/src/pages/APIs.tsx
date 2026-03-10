import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';
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
      <div className="p-6">
        <Loading message="Loading APIs..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-6">
        <Error
          message="Failed to load APIs"
          details={error as Error}
        />
      </div>
    );
  }

  const apis = data?.items || [];

  return (
    <div className="p-6">
      {/* Header */}
      {!selectedAPI ? (
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">API Inventory</h1>
          <p className="mt-2 text-sm text-gray-600">
            Browse and manage all discovered APIs across your gateways
          </p>
        </div>
      ) : (
        <div className="mb-6">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium mb-4"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to API List
          </button>
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