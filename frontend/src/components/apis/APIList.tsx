import { Search, Filter, AlertCircle, X, AlertTriangle, Info } from 'lucide-react';
import { useState, useEffect } from 'react';
import type { API, ComplianceViolation } from '../../types';
import { getComplianceViolations } from '../../services/compliance';

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
  initialShadowFilter?: boolean | 'all';
  initialHealthFilter?: string;
}

const APIList = ({
  apis,
  onSelectAPI,
  loading = false,
  initialShadowFilter = 'all',
  initialHealthFilter = 'all'
}: APIListProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [shadowFilter, setShadowFilter] = useState<boolean | 'all'>(initialShadowFilter);
  const [healthFilter, setHealthFilter] = useState<string>(initialHealthFilter);
  const [selectedAPI, setSelectedAPI] = useState<API | null>(null);
  const [violations, setViolations] = useState<ComplianceViolation[]>([]);
  const [loadingViolations, setLoadingViolations] = useState(false);
  const [showViolationsModal, setShowViolationsModal] = useState(false);

  // Filter APIs based on search and filters
  const filteredAPIs = apis.filter((api) => {
    const matchesSearch =
      api.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      api.base_path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      api.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const healthScore = api.intelligence_metadata?.health_score ?? 0;
    const isShadow = api.intelligence_metadata?.is_shadow ?? false;

    const matchesStatus = statusFilter === 'all' || api.status === statusFilter;
    const matchesShadow = shadowFilter === 'all' || isShadow === shadowFilter;
    
    const matchesHealth = healthFilter === 'all' ||
      (healthFilter === 'low' && healthScore < 70) ||
      (healthFilter === 'medium' && healthScore >= 70 && healthScore < 80) ||
      (healthFilter === 'high' && healthScore >= 80);

    return matchesSearch && matchesStatus && matchesShadow && matchesHealth;
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

  // Fetch violations for selected API
  const handleShowViolations = async (api: API) => {
    if (!api.intelligence_metadata?.violation_count) return;
    
    setSelectedAPI(api);
    setShowViolationsModal(true);
    setLoadingViolations(true);
    
    try {
      const response = await getComplianceViolations({
        api_id: api.id,
        gateway_id: api.gateway_id,
      });
      setViolations(response.violations);
    } catch (error) {
      console.error('Failed to fetch violations:', error);
      setViolations([]);
    } finally {
      setLoadingViolations(false);
    }
  };

  // Close modal
  const handleCloseModal = () => {
    setShowViolationsModal(false);
    setSelectedAPI(null);
    setViolations([]);
  };

  // Get severity color
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
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

        {/* Health Filter */}
        <select
          value={healthFilter}
          onChange={(e) => setHealthFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">All Health</option>
          <option value="high">High (≥80)</option>
          <option value="medium">Medium (70-79)</option>
          <option value="low">Low (less than 70)</option>
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
              } ${api.intelligence_metadata?.is_shadow ? 'border-l-4 border-l-orange-500' : ''}`}
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
                    {api.intelligence_metadata?.is_shadow && (
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
                    <span className="font-medium">Policies:</span>
                    <span>{api.policy_actions?.length || 0}</span>
                  </span>
                  <span
                    className={`flex items-center gap-1 ${
                      api.intelligence_metadata?.violation_count
                        ? 'cursor-pointer hover:underline'
                        : ''
                    }`}
                    onClick={(e) => {
                      if (api.intelligence_metadata?.violation_count) {
                        e.stopPropagation();
                        handleShowViolations(api);
                      }
                    }}
                  >
                    <span className="font-medium">Violations:</span>
                    <span className={api.intelligence_metadata?.violation_count ? 'text-red-600 font-semibold' : ''}>
                      {api.intelligence_metadata?.violation_count || 0}
                    </span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Risk:</span>
                    <span>{(api.intelligence_metadata?.risk_score ?? 0).toFixed(0)}</span>
                  </span>
                </div>

                {/* Health Score - Right Side */}
                <div className="text-center flex-shrink-0">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm ${getHealthColor(api.intelligence_metadata?.health_score ?? 0)}`}>
                    {(api.intelligence_metadata?.health_score ?? 0).toFixed(0)}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">Health</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Violations Modal */}
      {showViolationsModal && selectedAPI && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Compliance Violations
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  {selectedAPI.name} - {violations.length} violation{violations.length !== 1 ? 's' : ''}
                </p>
              </div>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {loadingViolations ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : violations.length === 0 ? (
                <div className="text-center py-12">
                  <Info className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600">No violations found</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {violations.map((violation) => (
                    <div
                      key={violation.id}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      {/* Violation Header */}
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <AlertTriangle className={`w-5 h-5 ${
                              violation.severity === 'critical' ? 'text-red-600' :
                              violation.severity === 'high' ? 'text-orange-600' :
                              violation.severity === 'medium' ? 'text-yellow-600' :
                              'text-blue-600'
                            }`} />
                            <h3 className="font-semibold text-gray-900">
                              {violation.title}
                            </h3>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">
                            {violation.description}
                          </p>
                        </div>
                        <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getSeverityColor(violation.severity)}`}>
                          {violation.severity.toUpperCase()}
                        </span>
                      </div>

                      {/* Violation Details */}
                      <div className="grid grid-cols-2 gap-4 text-sm mb-3">
                        <div>
                          <span className="font-medium text-gray-700">Standard:</span>
                          <span className="ml-2 text-gray-600">{violation.compliance_standard}</span>
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">Type:</span>
                          <span className="ml-2 text-gray-600">{violation.violation_type}</span>
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">Status:</span>
                          <span className={`ml-2 px-2 py-0.5 rounded text-xs ${
                            violation.status === 'open' ? 'bg-red-100 text-red-800' :
                            violation.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {violation.status.replace('_', ' ').toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">Risk Score:</span>
                          <span className="ml-2 text-gray-600">{violation.risk_score?.toFixed(1) || 'N/A'}</span>
                        </div>
                      </div>

                      {/* Regulation Reference */}
                      {violation.regulation_reference && (
                        <div className="mb-3">
                          <span className="font-medium text-gray-700 text-sm">Regulation:</span>
                          <p className="text-sm text-gray-600 mt-1">{violation.regulation_reference}</p>
                        </div>
                      )}

                      {/* Remediation Steps */}
                      {violation.remediation_steps && violation.remediation_steps.length > 0 && (
                        <div className="mb-3">
                          <span className="font-medium text-gray-700 text-sm">Remediation Steps:</span>
                          <ul className="list-disc list-inside text-sm text-gray-600 mt-1 space-y-1">
                            {violation.remediation_steps.map((step, idx) => (
                              <li key={idx}>{step}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Business Impact */}
                      {violation.business_impact && (
                        <div className="bg-gray-50 rounded p-3 text-sm">
                          <span className="font-medium text-gray-700">Business Impact:</span>
                          <p className="text-gray-600 mt-1">{violation.business_impact}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
              <button
                onClick={handleCloseModal}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default APIList;

// Made with Bob