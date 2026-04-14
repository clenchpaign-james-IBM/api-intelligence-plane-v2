import { useQuery } from '@tanstack/react-query';
import { Server, ChevronDown } from 'lucide-react';
import { api } from '../../services/api';
import type { Gateway } from '../../types';

/**
 * GatewaySelector Component
 * 
 * A reusable dropdown component for selecting a gateway across all pages.
 * Implements gateway-first navigation pattern where gateway is the primary scope.
 * 
 * Features:
 * - Fetches and displays all available gateways
 * - Shows gateway status with color indicators
 * - Supports "All Gateways" option
 * - Displays gateway vendor and connection status
 * - Responsive design with proper styling
 */

export interface GatewaySelectorProps {
  selectedGatewayId: string | null;
  onGatewayChange: (gatewayId: string | null) => void;
  className?: string;
  showAllOption?: boolean;
  label?: string;
}

const GatewaySelector = ({
  selectedGatewayId,
  onGatewayChange,
  className = '',
  showAllOption = true,
  label = 'Gateway',
}: GatewaySelectorProps) => {
  // Fetch gateways
  const { data: gatewaysData, isLoading } = useQuery({
    queryKey: ['gateways'],
    queryFn: () => api.gateways.list(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const gateways = gatewaysData?.items || [];
  const selectedGateway = gateways.find((g: Gateway) => g.id === selectedGatewayId);

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-green-500';
      case 'disconnected':
        return 'bg-gray-400';
      case 'maintenance':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  return (
    <div className={`relative ${className}`}>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>
      <div className="relative">
        <select
          value={selectedGatewayId || ''}
          onChange={(e) => onGatewayChange(e.target.value || null)}
          disabled={isLoading}
          className="block w-full pl-10 pr-10 py-2.5 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-lg bg-white shadow-sm disabled:bg-gray-100 disabled:cursor-not-allowed appearance-none cursor-pointer hover:border-gray-400 transition-colors"
        >
          {showAllOption && (
            <option value="">All Gateways</option>
          )}
          {gateways.map((gateway: Gateway) => (
            <option key={gateway.id} value={gateway.id}>
              {gateway.name} ({gateway.vendor}) - {gateway.status}
            </option>
          ))}
          {gateways.length === 0 && !isLoading && (
            <option value="" disabled>
              No gateways available
            </option>
          )}
        </select>
        
        {/* Icon on the left */}
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Server className="h-5 w-5 text-gray-400" />
        </div>
        
        {/* Chevron on the right */}
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
          <ChevronDown className="h-5 w-5 text-gray-400" />
        </div>
      </div>

      {/* Selected Gateway Info */}
      {selectedGateway && (
        <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${getStatusColor(selectedGateway.status)}`} />
              <span className="text-sm font-medium text-gray-900">
                {selectedGateway.name}
              </span>
            </div>
            <span className="text-xs text-gray-600 bg-white px-2 py-1 rounded">
              {selectedGateway.vendor}
            </span>
          </div>
          <p className="text-xs text-gray-600 mt-1 truncate">
            {selectedGateway.base_url}
          </p>
          {selectedGateway.last_connected_at && (
            <p className="text-xs text-gray-500 mt-1">
              Last connected: {new Date(selectedGateway.last_connected_at).toLocaleString()}
            </p>
          )}
        </div>
      )}

      {/* All Gateways Info */}
      {!selectedGatewayId && showAllOption && gateways.length > 0 && (
        <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">
              Viewing data from all gateways
            </span>
            <span className="text-xs text-gray-600 bg-white px-2 py-1 rounded">
              {gateways.length} gateway{gateways.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-sm text-gray-600">Loading gateways...</p>
        </div>
      )}

      {/* No Gateways State */}
      {!isLoading && gateways.length === 0 && (
        <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            No gateways configured. Add a gateway to start.
          </p>
        </div>
      )}
    </div>
  );
};

export default GatewaySelector;

// Made with Bob