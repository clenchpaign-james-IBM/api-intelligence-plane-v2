import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams, useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import APIList from '../components/apis/APIList';
import APIDetail from '../components/apis/APIDetail';
import Loading from '../components/common/Loading';
import Error from '../components/common/Error';
import GatewaySelector from '../components/common/GatewaySelector';
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
  const navigate = useNavigate();
  const { gatewayId, apiId } = useParams<{ gatewayId?: string; apiId?: string }>();
  const [selectedGatewayId, setSelectedGatewayId] = useState<string | null>(gatewayId || null);
  const [selectedAPI, setSelectedAPI] = useState<API | null>(null);
  const [searchParams] = useSearchParams();

  // Handle gateway selection
  const handleGatewayChange = (newGatewayId: string | null) => {
    setSelectedGatewayId(newGatewayId);
  };

  // Fetch APIs (filtered by gateway if selected)
  const { data, isLoading, error } = useQuery({
    queryKey: ['apis', selectedGatewayId],
    queryFn: () => {
      const params: any = {};
      // Only add gateway_id if a specific gateway is selected (not null/"All Gateways")
      if (selectedGatewayId && selectedGatewayId !== 'all') {
        params.gateway_id = selectedGatewayId;
      }
      return api.apis.list(params);
    },
    staleTime: 0, // Always fetch fresh data
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch specific API if apiId is in URL
  const { data: specificAPI } = useQuery({
    queryKey: ['api', apiId],
    queryFn: () => api.apis.get(apiId!),
    enabled: !!apiId,
    staleTime: 0,
  });

  // Set selected API when specific API is loaded from URL
  useEffect(() => {
    if (apiId && specificAPI && !selectedAPI) {
      setSelectedAPI(specificAPI);
    }
  }, [apiId, specificAPI, selectedAPI]);

  // Get initial filter from URL params
  const initialShadowFilter = searchParams.get('shadow');
  const initialHealthFilter = searchParams.get('health');

  // Handle API selection
  const handleSelectAPI = (api: API) => {
    setSelectedAPI(api);
  };

  // Handle back to list
  const handleBack = () => {
    setSelectedAPI(null);
    // If we came from a URL with apiId, navigate back to the list
    if (apiId) {
      navigate('/apis');
    }
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
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  const apis = data?.items || [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      {!selectedAPI ? (
        <>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">API Inventory</h1>
            <p className="mt-2 text-sm text-gray-600">
              Browse and manage all discovered APIs across your gateways
            </p>
          </div>
          
          {/* Gateway Selector */}
          <GatewaySelector
            selectedGatewayId={selectedGatewayId}
            onGatewayChange={handleGatewayChange}
            showAllOption={true}
          />
        </>
      ) : (
        <div>
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
          initialShadowFilter={initialShadowFilter === 'true' ? true : initialShadowFilter === 'false' ? false : 'all'}
          initialHealthFilter={initialHealthFilter || 'all'}
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