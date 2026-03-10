import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Zap, TrendingUp, Filter, DollarSign, Shield } from 'lucide-react';
import Loading from '../components/common/Loading';
import Error from '../components/common/Error';
import RateLimitPolicy from '../components/optimization/RateLimitPolicy';
import RateLimitChart from '../components/optimization/RateLimitChart';
import { api } from '../services/api';
import type {
  Recommendation,
  RecommendationPriority,
  RecommendationStatus,
  RecommendationType,
  RateLimitPolicy as RateLimitPolicyType,
  PolicyStatus
} from '../types';

/**
 * Optimization Page
 *
 * Displays performance optimization recommendations and rate limiting policies with:
 * - Tab-based interface for recommendations and rate limiting
 * - List of active recommendations
 * - Filtering by priority, status, and type
 * - Statistics and potential savings
 * - Rate limit policy management
 * - Effectiveness analysis
 */
const Optimization = () => {
  const [activeTab, setActiveTab] = useState<'recommendations' | 'rate-limiting'>('recommendations');
  const [selectedPriority, setSelectedPriority] = useState<RecommendationPriority | 'all'>('all');
  const [selectedStatus, setSelectedStatus] = useState<RecommendationStatus | 'all'>('all');
  const [selectedType, setSelectedType] = useState<RecommendationType | 'all'>('all');
  const [selectedRecommendation, setSelectedRecommendation] = useState<Recommendation | null>(null);
  const [selectedPolicy, setSelectedPolicy] = useState<RateLimitPolicyType | null>(null);
  const [selectedPolicyStatus, setSelectedPolicyStatus] = useState<PolicyStatus | 'all'>('all');
  
  const queryClient = useQueryClient();

  // Fetch recommendations
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['recommendations', selectedPriority, selectedStatus, selectedType],
    queryFn: () => {
      const params: any = {};
      if (selectedPriority !== 'all') params.priority = selectedPriority;
      if (selectedStatus !== 'all') params.status = selectedStatus;
      if (selectedType !== 'all') params.recommendation_type = selectedType;
      return api.recommendations.list(params);
    },
    refetchInterval: 60000, // Refetch every minute
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['recommendation-stats'],
    queryFn: () => api.recommendations.stats(),
    refetchInterval: 60000,
  });

  // Fetch rate limit policies
  const { data: rateLimitData, isLoading: rateLimitLoading, error: rateLimitError } = useQuery({
    queryKey: ['rate-limits', selectedPolicyStatus],
    queryFn: () => {
      const params: any = {};
      if (selectedPolicyStatus !== 'all') params.status = selectedPolicyStatus;
      return api.rateLimits.list(params);
    },
    refetchInterval: 60000,
    enabled: activeTab === 'rate-limiting',
  });

  // Fetch effectiveness for selected policy
  const { data: effectivenessData } = useQuery({
    queryKey: ['rate-limit-effectiveness', selectedPolicy?.id],
    queryFn: () => selectedPolicy ? api.rateLimits.effectiveness(selectedPolicy.id) : null,
    enabled: !!selectedPolicy && activeTab === 'rate-limiting',
  });

  // Activate policy mutation
  const activateMutation = useMutation({
    mutationFn: (policyId: string) => api.rateLimits.activate(policyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rate-limits'] });
    },
  });

  // Deactivate policy mutation
  const deactivateMutation = useMutation({
    mutationFn: (policyId: string) => api.rateLimits.deactivate(policyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rate-limits'] });
    },
  });

  // Loading state
  if (isLoading) {
    return (
      <div className="p-6">
        <Loading message="Loading optimization recommendations..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-6">
        <Error
          message="Failed to load recommendations"
          details={error as Error}
        />
      </div>
    );
  }

  const recommendations = data?.recommendations || [];
  const total = data?.total || 0;
  const pendingCount = recommendations.filter((r: Recommendation) => r.status === 'pending').length;
  const highPriorityCount = recommendations.filter((r: Recommendation) => 
    r.priority === 'critical' || r.priority === 'high'
  ).length;
  const totalSavings = stats?.total_cost_savings || 0;
  const avgImprovement = stats?.avg_improvement || 0;

  // Priority badge color
  const getPriorityColor = (priority: RecommendationPriority) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Status badge color
  const getStatusColor = (status: RecommendationStatus) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'implemented': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-gray-100 text-gray-800';
      case 'expired': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Type display name
  const getTypeDisplayName = (type: RecommendationType) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Performance Optimization</h1>
            <p className="mt-2 text-sm text-gray-600">
              AI-powered recommendations and intelligent rate limiting
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <TrendingUp className="w-5 h-5" />
            Refresh
          </button>
        </div>

        {/* Tabs */}
        <div className="mt-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`${
                activeTab === 'recommendations'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
            >
              <Zap className="w-5 h-5" />
              Recommendations
            </button>
            <button
              onClick={() => setActiveTab('rate-limiting')}
              className={`${
                activeTab === 'rate-limiting'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
            >
              <Shield className="w-5 h-5" />
              Rate Limiting
            </button>
          </nav>
        </div>

        {/* Stats */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending Actions</p>
                <p className="text-2xl font-bold text-gray-900">{pendingCount}</p>
              </div>
              <Zap className="w-8 h-8 text-yellow-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">High Priority</p>
                <p className="text-2xl font-bold text-orange-600">{highPriorityCount}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Improvement</p>
                <p className="text-2xl font-bold text-green-600">{avgImprovement.toFixed(1)}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Potential Savings</p>
                <p className="text-2xl font-bold text-blue-600">${totalSavings.toFixed(0)}/mo</p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations Tab Content */}
      {activeTab === 'recommendations' && (
        <>
          {/* Filters */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="flex items-center gap-4 flex-wrap">
          <Filter className="w-5 h-5 text-gray-500" />
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Priority:</label>
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value as RecommendationPriority | 'all')}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Status:</label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as RecommendationStatus | 'all')}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="implemented">Implemented</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Type:</label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as RecommendationType | 'all')}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All</option>
              <option value="caching">Caching</option>
              <option value="query_optimization">Query Optimization</option>
              <option value="resource_allocation">Resource Allocation</option>
              <option value="compression">Compression</option>
              <option value="connection_pooling">Connection Pooling</option>
            </select>
          </div>
        </div>
          </div>

          {/* Recommendations List */}
          <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recommendations</h2>
        {recommendations.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <Zap className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No recommendations found</p>
            <p className="text-sm text-gray-500 mt-2">
              Recommendations are generated automatically every 30 minutes
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {recommendations.map((recommendation: Recommendation) => (
              <div
                key={recommendation.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => setSelectedRecommendation(recommendation)}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {recommendation.title}
                    </h3>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {recommendation.description}
                    </p>
                  </div>
                </div>

                {/* Badges */}
                <div className="flex items-center gap-2 mb-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(recommendation.priority)}`}>
                    {recommendation.priority.toUpperCase()}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(recommendation.status)}`}>
                    {recommendation.status.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                    {getTypeDisplayName(recommendation.recommendation_type)}
                  </span>
                </div>

                {/* Impact */}
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Expected Impact</span>
                    <span className="text-lg font-bold text-green-600">
                      +{recommendation.estimated_impact.improvement_percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-xs text-gray-600">
                    <div className="flex justify-between">
                      <span>Current: {recommendation.estimated_impact.current_value.toFixed(2)}ms</span>
                      <span>Expected: {recommendation.estimated_impact.expected_value.toFixed(2)}ms</span>
                    </div>
                    <div className="mt-1">
                      Confidence: {(recommendation.estimated_impact.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>

                {/* Effort & Savings */}
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600">Effort:</span>
                    <span className="font-medium text-gray-900 capitalize">
                      {recommendation.implementation_effort}
                    </span>
                  </div>
                  {recommendation.cost_savings && (
                    <div className="flex items-center gap-1 text-blue-600 font-medium">
                      <DollarSign className="w-4 h-4" />
                      {recommendation.cost_savings.toFixed(0)}/mo
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
          </div>

          {/* Detailed View Modal */}
          {selectedRecommendation && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedRecommendation(null)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              {/* Header */}
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  {selectedRecommendation.title}
                </h2>
                <p className="text-gray-600">{selectedRecommendation.description}</p>
                <div className="flex items-center gap-2 mt-4">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(selectedRecommendation.priority)}`}>
                    {selectedRecommendation.priority.toUpperCase()}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedRecommendation.status)}`}>
                    {selectedRecommendation.status.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                    {getTypeDisplayName(selectedRecommendation.recommendation_type)}
                  </span>
                </div>
              </div>

              {/* Impact Details */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Expected Impact</h3>
                <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Current Value</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {selectedRecommendation.estimated_impact.current_value.toFixed(2)}ms
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Expected Value</p>
                      <p className="text-2xl font-bold text-green-600">
                        {selectedRecommendation.estimated_impact.expected_value.toFixed(2)}ms
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Improvement</p>
                      <p className="text-2xl font-bold text-blue-600">
                        +{selectedRecommendation.estimated_impact.improvement_percentage.toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Confidence</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {(selectedRecommendation.estimated_impact.confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Implementation Steps */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Implementation Steps</h3>
                <ol className="space-y-2">
                  {selectedRecommendation.implementation_steps.map((step, index) => (
                    <li key={index} className="flex gap-3">
                      <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </span>
                      <span className="text-gray-700 pt-0.5">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>

              {/* Additional Info */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Implementation Effort</p>
                  <p className="text-lg font-semibold text-gray-900 capitalize">
                    {selectedRecommendation.implementation_effort}
                  </p>
                </div>
                {selectedRecommendation.cost_savings && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 mb-1">Monthly Savings</p>
                    <p className="text-lg font-semibold text-green-600">
                      ${selectedRecommendation.cost_savings.toFixed(2)}
                    </p>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={() => setSelectedRecommendation(null)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Close
                </button>
                <button
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  onClick={() => {
                    // TODO: Implement mark as in progress
                    alert('Mark as in progress - to be implemented');
                  }}
                >
                  Start Implementation
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
        </>
      )}
          
      {/* Rate Limiting Tab Content */}
      {activeTab === 'rate-limiting' && (
                  <>
                    {/* Rate Limiting Stats */}
                    <div className="mb-6">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-white rounded-lg shadow p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm text-gray-600">Active Policies</p>
                              <p className="text-2xl font-bold text-gray-900">
                                {rateLimitData?.items?.filter((p: RateLimitPolicyType) => p.status === 'active').length || 0}
                              </p>
                            </div>
                            <Shield className="w-8 h-8 text-green-500" />
                          </div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm text-gray-600">Total Policies</p>
                              <p className="text-2xl font-bold text-gray-900">{rateLimitData?.total || 0}</p>
                            </div>
                            <Shield className="w-8 h-8 text-blue-500" />
                          </div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm text-gray-600">Avg Effectiveness</p>
                              <p className="text-2xl font-bold text-green-600">
                                {rateLimitData?.items?.length > 0
                                  ? (
                                      (rateLimitData.items
                                        .filter((p: RateLimitPolicyType) => p.effectiveness_score !== undefined)
                                        .reduce((sum: number, p: RateLimitPolicyType) => sum + (p.effectiveness_score || 0), 0) /
                                        rateLimitData.items.filter((p: RateLimitPolicyType) => p.effectiveness_score !== undefined).length) *
                                      100
                                    ).toFixed(0)
                                  : 0}
                                %
                              </p>
                            </div>
                            <TrendingUp className="w-8 h-8 text-green-500" />
                          </div>
                        </div>
                      </div>
                    </div>
          
                    {/* Filters */}
                    <div className="mb-6 bg-white rounded-lg shadow p-4">
                      <div className="flex items-center gap-4 flex-wrap">
                        <Filter className="w-5 h-5 text-gray-500" />
                        <div className="flex items-center gap-2">
                          <label className="text-sm font-medium text-gray-700">Status:</label>
                          <select
                            value={selectedPolicyStatus}
                            onChange={(e) => setSelectedPolicyStatus(e.target.value as PolicyStatus | 'all')}
                            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="all">All</option>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="testing">Testing</option>
                          </select>
                        </div>
                      </div>
                    </div>
          
                    {/* Rate Limit Policies List */}
                    <div>
                      <h2 className="text-xl font-bold text-gray-900 mb-4">Rate Limit Policies</h2>
                      {rateLimitLoading ? (
                        <Loading message="Loading rate limit policies..." />
                      ) : rateLimitError ? (
                        <Error message="Failed to load rate limit policies" details={rateLimitError as Error} />
                      ) : !rateLimitData?.items || rateLimitData.items.length === 0 ? (
                        <div className="bg-white rounded-lg shadow p-8 text-center">
                          <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                          <p className="text-gray-600">No rate limit policies found</p>
                          <p className="text-sm text-gray-500 mt-2">
                            Create policies to protect your APIs from excessive traffic
                          </p>
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                          {rateLimitData.items.map((policy: RateLimitPolicyType) => (
                            <div key={policy.id} onClick={() => setSelectedPolicy(policy)}>
                              <RateLimitPolicy
                                policy={policy}
                                onActivate={(id) => activateMutation.mutate(id)}
                                onDeactivate={(id) => deactivateMutation.mutate(id)}
                              />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
          
                    {/* Policy Detail Modal */}
                    {selectedPolicy && (
                      <div
                        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
                        onClick={() => setSelectedPolicy(null)}
                      >
                        <div
                          className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="p-6">
                            <RateLimitPolicy
                              policy={selectedPolicy}
                              detailed={true}
                              onActivate={(id) => {
                                activateMutation.mutate(id);
                                setSelectedPolicy(null);
                              }}
                              onDeactivate={(id) => {
                                deactivateMutation.mutate(id);
                                setSelectedPolicy(null);
                              }}
                            />
          
                            {/* Effectiveness Chart */}
                            {effectivenessData && (
                              <div className="mt-6">
                                <RateLimitChart effectiveness={effectivenessData} />
                              </div>
                            )}
          
                            {/* Close Button */}
                            <div className="mt-6">
                              <button
                                onClick={() => setSelectedPolicy(null)}
                                className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                              >
                                Close
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}
    </div>
  );
};

export default Optimization;

// Made with Bob