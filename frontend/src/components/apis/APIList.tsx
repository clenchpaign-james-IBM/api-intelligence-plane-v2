import { Search, Filter, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import type { API } from '../../types';

/**
 * API List Component
 * 
 * Displays a filterable list of APIs with search and status filtering.
 * Shows key metrics and health indicators for each API.
 */

interface APIListProps {
  apis: API[];
  onSelectAPI?: (api: API) => void;
  loading?: boolean;
}

const APIList = ({ apis, onSelectAPI, loading = false }: APIListProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [shadowFilter, setShadowFilter] = useState<boolean | 'all'>('all');

  // Filter APIs based on search and filters
  const filteredAPIs = apis.filter((api) => {
    const matchesSearch = 
      api.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      api.base_path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      api.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesStatus = statusFilter === 'all' || api.status === statusFilter;
    const matchesShadow = shadowFilter === 'all' || api.is_shadow === shadowFilter;

    return matchesSearch && matchesStatus && matchesShadow;
  });

  // Get health score color
  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 50) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'deprecated': return 'bg-orange-100 text-orange-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search APIs by name, path, or tags..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <Filter className="text-gray-400 w-5 h-5" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="deprecated">Deprecated</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {/* Shadow Filter */}
        <select
          value={shadowFilter.toString()}
          onChange={(e) => setShadowFilter(e.target.value === 'all' ? 'all' : e.target.value === 'true')}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">All APIs</option>
          <option value="false">Documented</option>
          <option value="true">Shadow APIs</option>
        </select>
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-600">
        Showing {filteredAPIs.length} of {apis.length} APIs
      </div>

      {/* API List */}
      {filteredAPIs.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600">No APIs found matching your criteria</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredAPIs.map((api) => (
            <div
              key={api.id}
              onClick={() => onSelectAPI?.(api)}
              className={`px-4 py-2.5 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-sm transition-all ${
                onSelectAPI ? 'cursor-pointer' : ''
              } ${api.is_shadow ? 'border-l-4 border-l-orange-500' : ''}`}
            >
              <div className="flex items-center justify-between gap-4">
                {/* API Name & Path */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <h3 className="text-base font-bold text-gray-900 truncate">{api.name}</h3>
                    {api.version && (
                      <span className="px-1.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded flex-shrink-0">
                        v{api.version}
                      </span>
                    )}
                    <span className={`px-1.5 py-0.5 text-xs font-medium rounded flex-shrink-0 ${getStatusColor(api.status)}`}>
                      {api.status}
                    </span>
                    {api.is_shadow && (
                      <span className="px-1.5 py-0.5 text-xs font-medium bg-orange-100 text-orange-800 rounded flex-shrink-0">
                        Shadow
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 truncate">{api.base_path}</p>
                </div>

                {/* Tags - Compact */}
                {api.tags && api.tags.length > 0 && (
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {api.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="px-1.5 py-0.5 text-xs bg-blue-50 text-blue-700 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                    {api.tags.length > 3 && (
                      <span className="px-1.5 py-0.5 text-xs text-gray-500">
                        +{api.tags.length - 3}
                      </span>
                    )}
                  </div>
                )}

                {/* Metrics - Horizontal Compact */}
                <div className="flex items-center gap-4 text-xs text-gray-600 flex-shrink-0">
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Endpoints:</span>
                    <span>{api.endpoints.length}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Methods:</span>
                    <span>{api.methods.join(', ')}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Auth:</span>
                    <span className="truncate max-w-[80px]">{api.authentication_type}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium">P95:</span>
                    <span>{api.current_metrics.response_time_p95.toFixed(0)}ms</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Error:</span>
                    <span>{(api.current_metrics.error_rate * 100).toFixed(1)}%</span>
                  </span>
                </div>

                {/* Health Score - Right Side */}
                <div className="text-center flex-shrink-0">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm ${getHealthColor(api.health_score)}`}>
                    {api.health_score.toFixed(0)}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">Health</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default APIList;

// Made with Bob