import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Heading, Button, Toggle, Select, SelectItem, Tabs, TabList, Tab, TabPanels, TabPanel, Tag, ClickableTile } from '@carbon/react';
import { Zap, TrendingUp, Filter, DollarSign, Shield, Sparkles, CurrencyDollar } from '../utils/carbonIcons';
import Card from '../components/common/Card';
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
  const [useAi, setUseAi] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  
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

  // Apply policy mutation
  const applyMutation = useMutation({
    mutationFn: (policyId: string) => api.rateLimits.apply(policyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rate-limits'] });
      alert('Rate limit policy applied to Gateway successfully!');
    },
    onError: (error: any) => {
      alert(`Failed to apply policy: ${error.message || 'Unknown error'}`);
    },
  });

  // Loading state
  if (isLoading) {
    return (
      <div style={{ padding: 'var(--cds-spacing-06)' }}>
        <Loading message="Loading optimization recommendations..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{ padding: 'var(--cds-spacing-06)' }}>
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

  // Priority tag type
  const getPriorityTagType = (priority: RecommendationPriority): 'red' | 'magenta' | 'purple' | 'blue' | 'gray' => {
    switch (priority) {
      case 'critical': return 'red';
      case 'high': return 'magenta';
      case 'medium': return 'purple';
      case 'low': return 'blue';
      default: return 'gray';
    }
  };

  // Status tag type
  const getStatusTagType = (status: RecommendationStatus): 'warm-gray' | 'blue' | 'green' | 'gray' | 'red' => {
    switch (status) {
      case 'pending': return 'warm-gray';
      case 'in_progress': return 'blue';
      case 'implemented': return 'green';
      case 'rejected': return 'gray';
      case 'expired': return 'red';
      default: return 'gray';
    }
  };

  // Type display name
  const getTypeDisplayName = (type: RecommendationType) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div style={{ padding: 'var(--cds-spacing-06)' }}>
      {/* Header */}
      <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--cds-spacing-06)' }}>
          <div>
            <Heading>Performance Optimization</Heading>
            <p style={{ marginTop: 'var(--cds-spacing-03)', fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>
              {useAi ? 'LLM-enhanced recommendations with detailed insights' : 'Rule-based recommendations'} and intelligent rate limiting
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
            {/* AI Toggle Switch */}
            {activeTab === 'recommendations' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)', padding: 'var(--cds-spacing-04)', backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px' }}>
                <Sparkles size={20} style={{ color: useAi ? 'var(--cds-support-info)' : 'var(--cds-icon-secondary)' }} />
                <Toggle
                  id="ai-toggle-opt"
                  labelText="AI Enhanced"
                  toggled={useAi}
                  onToggle={() => setUseAi(!useAi)}
                  size="sm"
                />
              </div>
            )}
            <Button
              kind="primary"
              renderIcon={TrendingUp}
              onClick={() => {
                setIsGenerating(true);
                refetch().finally(() => setIsGenerating(false));
              }}
              disabled={isGenerating}
            >
              {isGenerating ? 'Refreshing...' : 'Refresh List'}
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <Tabs selectedIndex={activeTab === 'recommendations' ? 0 : 1} onChange={(e) => setActiveTab(e.selectedIndex === 0 ? 'recommendations' : 'rate-limiting')}>
          <TabList aria-label="Optimization tabs">
            <Tab renderIcon={Zap}>Recommendations</Tab>
            <Tab renderIcon={Shield}>Rate Limiting</Tab>
          </TabList>
        </Tabs>
      </div>

      {/* Recommendations Tab Content */}
      {activeTab === 'recommendations' && (
        <>
          {/* Stats */}
          <div style={{ marginBottom: 'var(--cds-spacing-08)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--cds-spacing-06)' }}>
            <Card padding="md">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Pending Actions</p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>{pendingCount}</p>
                </div>
                <Zap size={32} style={{ color: 'var(--cds-support-warning)' }} />
              </div>
            </Card>
            <Card padding="md">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>High Priority</p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-support-error)' }}>{highPriorityCount}</p>
                </div>
                <TrendingUp size={32} style={{ color: 'var(--cds-support-error)' }} />
              </div>
            </Card>
            <Card padding="md">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Avg Improvement</p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-support-success)' }}>{avgImprovement.toFixed(1)}%</p>
                </div>
                <TrendingUp size={32} style={{ color: 'var(--cds-support-success)' }} />
              </div>
            </Card>
            <Card padding="md">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Potential Savings</p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-link-primary)' }}>${totalSavings.toFixed(0)}/mo</p>
                </div>
                <DollarSign size={32} style={{ color: 'var(--cds-link-primary)' }} />
              </div>
            </Card>
          </div>

          {/* Filters */}
          <div style={{ marginBottom: 'var(--cds-spacing-08)' }}>
            <Card padding="md">
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-06)', flexWrap: 'wrap' }}>
                <Filter size={20} style={{ color: 'var(--cds-icon-secondary)' }} />
                <Select
                  id="priority-select"
                  labelText="Priority"
                  value={selectedPriority}
                  onChange={(e) => setSelectedPriority(e.target.value as RecommendationPriority | 'all')}
                  size="sm"
                  inline
                >
                  <SelectItem value="all" text="All" />
                  <SelectItem value="critical" text="Critical" />
                  <SelectItem value="high" text="High" />
                  <SelectItem value="medium" text="Medium" />
                  <SelectItem value="low" text="Low" />
                </Select>
                <Select
                  id="status-select"
                  labelText="Status"
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value as RecommendationStatus | 'all')}
                  size="sm"
                  inline
                >
                  <SelectItem value="all" text="All" />
                  <SelectItem value="pending" text="Pending" />
                  <SelectItem value="in_progress" text="In Progress" />
                  <SelectItem value="implemented" text="Implemented" />
                  <SelectItem value="rejected" text="Rejected" />
                </Select>
                <Select
                  id="type-select"
                  labelText="Type"
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value as RecommendationType | 'all')}
                  size="sm"
                  inline
                >
                  <SelectItem value="all" text="All" />
                  <SelectItem value="caching" text="Caching" />
                  <SelectItem value="query_optimization" text="Query Optimization" />
                  <SelectItem value="resource_allocation" text="Resource Allocation" />
                  <SelectItem value="compression" text="Compression" />
                  <SelectItem value="connection_pooling" text="Connection Pooling" />
                </Select>
              </div>
            </Card>
          </div>

          {/* Recommendations List */}
          <div>
            <Heading style={{ fontSize: '1.25rem', marginBottom: 'var(--cds-spacing-06)' }}>Recommendations</Heading>
            {recommendations.length === 0 ? (
              <Card padding="lg">
                <div style={{ textAlign: 'center' }}>
                  <Zap size={48} style={{ color: 'var(--cds-icon-secondary)', margin: '0 auto var(--cds-spacing-05)' }} />
                  <p style={{ color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-03)' }}>No recommendations found</p>
                  <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-helper)' }}>
                    Recommendations are generated automatically every 30 minutes
                  </p>
                </div>
              </Card>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-07)' }}>
                {recommendations.map((recommendation: Recommendation, index: number) => (
                  <ClickableTile
                    key={recommendation.id}
                    onClick={() => setSelectedRecommendation(recommendation)}
                    style={{
                      padding: 'var(--cds-spacing-06)',
                      border: '1px solid var(--cds-border-subtle)',
                      borderRadius: '4px',
                      marginBottom: index < recommendations.length - 1 ? 'var(--cds-spacing-07)' : '0'
                    }}
                  >
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 'var(--cds-spacing-05)' }}>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-03)' }}>
                      {recommendation.title}
                    </h3>
                    <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', lineHeight: '1.5' }}>
                      {recommendation.description}
                    </p>
                  </div>
                </div>

                {/* Badges */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)', marginBottom: 'var(--cds-spacing-05)' }}>
                  <Tag type={getPriorityTagType(recommendation.priority)} size="sm">
                    {recommendation.priority.toUpperCase()}
                  </Tag>
                  <Tag type={getStatusTagType(recommendation.status)} size="sm">
                    {recommendation.status.replace('_', ' ').toUpperCase()}
                  </Tag>
                  <Tag type="purple" size="sm">
                    {getTypeDisplayName(recommendation.recommendation_type)}
                  </Tag>
                </div>

                {/* Impact */}
                <div style={{
                  backgroundColor: 'var(--cds-layer-01)',
                  borderRadius: 'var(--cds-spacing-02)',
                  padding: 'var(--cds-spacing-05)',
                  marginBottom: 'var(--cds-spacing-05)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--cds-spacing-03)' }}>
                    <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--cds-text-secondary)' }}>Expected Impact</span>
                    <span style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-support-success)' }}>
                      +{recommendation.estimated_impact.improvement_percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Current: {recommendation.estimated_impact.current_value.toFixed(2)}ms</span>
                      <span>Expected: {recommendation.estimated_impact.expected_value.toFixed(2)}ms</span>
                    </div>
                    <div style={{ marginTop: 'var(--cds-spacing-02)' }}>
                      Confidence: {(recommendation.estimated_impact.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>

                {/* Effort & Savings */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
                    <span style={{ color: 'var(--cds-text-secondary)' }}>Effort:</span>
                    <span style={{ fontWeight: 500, color: 'var(--cds-text-primary)', textTransform: 'capitalize' }}>
                      {recommendation.implementation_effort}
                    </span>
                  </div>
                  {recommendation.cost_savings && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-02)', color: 'var(--cds-link-primary)', fontWeight: 500 }}>
                      <CurrencyDollar size={16} />
                      {recommendation.cost_savings.toFixed(0)}/mo
                    </div>
                  )}
                </div>
              </ClickableTile>
            ))}
          </div>
        )}
          </div>

          {/* Detailed View Modal */}
          {selectedRecommendation && (
            <div
              style={{
                position: 'fixed',
                inset: 0,
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 'var(--cds-spacing-05)',
                zIndex: 9999
              }}
              onClick={() => setSelectedRecommendation(null)}
            >
              <div
                style={{
                  backgroundColor: 'var(--cds-layer-01)',
                  borderRadius: 'var(--cds-spacing-02)',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                  maxWidth: '1024px',
                  width: '100%',
                  maxHeight: '90vh',
                  overflowY: 'auto'
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <div style={{ padding: 'var(--cds-spacing-07)' }}>
              {/* Header */}
              <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-03)' }}>
                  {selectedRecommendation.title}
                </h2>
                <p style={{ color: 'var(--cds-text-secondary)' }}>{selectedRecommendation.description}</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)', marginTop: 'var(--cds-spacing-05)' }}>
                  <Tag type={getPriorityTagType(selectedRecommendation.priority)}>
                    {selectedRecommendation.priority.toUpperCase()}
                  </Tag>
                  <Tag type={getStatusTagType(selectedRecommendation.status)}>
                    {selectedRecommendation.status.replace('_', ' ').toUpperCase()}
                  </Tag>
                  <Tag type="purple">
                    {getTypeDisplayName(selectedRecommendation.recommendation_type)}
                  </Tag>
                </div>
              </div>

              {/* Impact Details */}
              <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-05)' }}>Expected Impact</h3>
                <div style={{
                  background: 'linear-gradient(to right, var(--cds-layer-01), var(--cds-layer-02))',
                  borderRadius: 'var(--cds-spacing-02)',
                  padding: 'var(--cds-spacing-05)'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--cds-spacing-05)' }}>
                    <div>
                      <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Current Value</p>
                      <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                        {selectedRecommendation.estimated_impact.current_value.toFixed(2)}ms
                      </p>
                    </div>
                    <div>
                      <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Expected Value</p>
                      <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-support-success)' }}>
                        {selectedRecommendation.estimated_impact.expected_value.toFixed(2)}ms
                      </p>
                    </div>
                    <div>
                      <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Improvement</p>
                      <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-link-primary)' }}>
                        +{selectedRecommendation.estimated_impact.improvement_percentage.toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Confidence</p>
                      <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-support-info)' }}>
                        {(selectedRecommendation.estimated_impact.confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Implementation Steps */}
              <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-05)' }}>Implementation Steps</h3>
                <ol style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-03)' }}>
                  {selectedRecommendation.implementation_steps.map((step, index) => (
                    <li key={index} style={{ display: 'flex', gap: 'var(--cds-spacing-04)' }}>
                      <span style={{
                        flexShrink: 0,
                        width: '24px',
                        height: '24px',
                        backgroundColor: 'var(--cds-link-primary)',
                        color: 'var(--cds-text-on-color)',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.875rem',
                        fontWeight: 500
                      }}>
                        {index + 1}
                      </span>
                      <span style={{ color: 'var(--cds-text-secondary)', paddingTop: '2px' }}>{step}</span>
                    </li>
                  ))}
                </ol>
              </div>

              {/* Additional Info */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--cds-spacing-05)', marginBottom: 'var(--cds-spacing-07)' }}>
                <div style={{ backgroundColor: 'var(--cds-layer-01)', borderRadius: 'var(--cds-spacing-02)', padding: 'var(--cds-spacing-05)' }}>
                  <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Implementation Effort</p>
                  <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)', textTransform: 'capitalize' }}>
                    {selectedRecommendation.implementation_effort}
                  </p>
                </div>
                {selectedRecommendation.cost_savings && (
                  <div style={{ backgroundColor: 'var(--cds-layer-01)', borderRadius: 'var(--cds-spacing-02)', padding: 'var(--cds-spacing-05)' }}>
                    <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Monthly Savings</p>
                    <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-support-success)' }}>
                      ${selectedRecommendation.cost_savings.toFixed(2)}
                    </p>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: 'var(--cds-spacing-04)' }}>
                <Button
                  kind="secondary"
                  onClick={() => setSelectedRecommendation(null)}
                  style={{ flex: 1 }}
                >
                  Close
                </Button>
                <Button
                  kind="primary"
                  onClick={() => {
                    // TODO: Implement mark as in progress
                    alert('Mark as in progress - to be implemented');
                  }}
                  style={{ flex: 1 }}
                >
                  Start Implementation
                </Button>
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
                    <div style={{ marginBottom: 'var(--cds-spacing-08)' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 'var(--cds-spacing-06)' }}>
                        <div style={{ padding: 'var(--cds-spacing-05)' }}>
                          <Card>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <div>
                                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Active Policies</p>
                                <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                                  {rateLimitData?.items?.filter((p: RateLimitPolicyType) => p.status === 'active').length || 0}
                                </p>
                              </div>
                              <Shield size={32} style={{ color: 'var(--cds-support-success)' }} />
                            </div>
                          </Card>
                        </div>
                        <div style={{ padding: 'var(--cds-spacing-05)' }}>
                          <Card>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <div>
                                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Total Policies</p>
                                <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>{rateLimitData?.total || 0}</p>
                              </div>
                              <Shield size={32} style={{ color: 'var(--cds-link-primary)' }} />
                            </div>
                          </Card>
                        </div>
                        <div style={{ padding: 'var(--cds-spacing-05)' }}>
                          <Card>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <div>
                                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Avg Effectiveness</p>
                                <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-support-success)' }}>
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
                              <TrendingUp size={32} style={{ color: 'var(--cds-support-success)' }} />
                            </div>
                          </Card>
                        </div>
                      </div>
                    </div>
          
                    {/* Filters */}
                    <div style={{ marginBottom: 'var(--cds-spacing-08)' }}>
                      <div style={{ padding: 'var(--cds-spacing-05)' }}>
                        <Card>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-05)', flexWrap: 'wrap' }}>
                            <Filter size={20} style={{ color: 'var(--cds-icon-secondary)' }} />
                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
                              <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--cds-text-secondary)' }}>Status:</label>
                              <Select
                                id="policy-status-filter"
                                value={selectedPolicyStatus}
                                onChange={(e) => setSelectedPolicyStatus(e.target.value as PolicyStatus | 'all')}
                                size="sm"
                              >
                                <SelectItem value="all" text="All" />
                                <SelectItem value="active" text="Active" />
                                <SelectItem value="inactive" text="Inactive" />
                                <SelectItem value="testing" text="Testing" />
                              </Select>
                            </div>
                          </div>
                        </Card>
                      </div>
                    </div>
          
                    {/* Rate Limit Policies List */}
                    <div>
                      <Heading style={{ marginBottom: 'var(--cds-spacing-06)' }}>Rate Limit Policies</Heading>
                      {rateLimitLoading ? (
                        <Loading message="Loading rate limit policies..." />
                      ) : rateLimitError ? (
                        <Error message="Failed to load rate limit policies" details={rateLimitError as Error} />
                      ) : !rateLimitData?.items || rateLimitData.items.length === 0 ? (
                        <div style={{ padding: 'var(--cds-spacing-05)' }}>
                          <Card>
                            <div style={{ padding: 'var(--cds-spacing-07)', textAlign: 'center' }}>
                              <Shield size={48} style={{ color: 'var(--cds-icon-disabled)', margin: '0 auto var(--cds-spacing-05)' }} />
                              <p style={{ color: 'var(--cds-text-secondary)' }}>No rate limit policies found</p>
                              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginTop: 'var(--cds-spacing-03)' }}>
                                Create policies to protect your APIs from excessive traffic
                              </p>
                            </div>
                          </Card>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-07)' }}>
                          {rateLimitData.items.map((policy: RateLimitPolicyType, index: number) => (
                            <div key={policy.id} onClick={() => setSelectedPolicy(policy)} style={{ marginBottom: index < rateLimitData.items.length - 1 ? 'var(--cds-spacing-07)' : '0' }}>
                              <RateLimitPolicy
                                policy={policy}
                                onActivate={(id) => activateMutation.mutate(id)}
                                onDeactivate={(id) => deactivateMutation.mutate(id)}
                                onApply={(id) => applyMutation.mutate(id)}
                              />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
          
                    {/* Policy Detail Modal */}
                    {selectedPolicy && (
                      <div
                        style={{
                          position: 'fixed',
                          inset: 0,
                          backgroundColor: 'rgba(0, 0, 0, 0.5)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          padding: 'var(--cds-spacing-05)',
                          zIndex: 9999
                        }}
                        onClick={() => setSelectedPolicy(null)}
                      >
                        <div
                          style={{
                            backgroundColor: 'var(--cds-layer-01)',
                            borderRadius: 'var(--cds-spacing-02)',
                            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                            maxWidth: '1024px',
                            width: '100%',
                            maxHeight: '90vh',
                            overflowY: 'auto'
                          }}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div style={{ padding: 'var(--cds-spacing-07)' }}>
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
                              onApply={(id) => {
                                applyMutation.mutate(id);
                                setSelectedPolicy(null);
                              }}
                            />
          
                            {/* Effectiveness Chart */}
                            {effectivenessData && (
                              <div style={{ marginTop: 'var(--cds-spacing-07)' }}>
                                <RateLimitChart effectiveness={effectivenessData} />
                              </div>
                            )}
          
                            {/* Close Button */}
                            <div style={{ marginTop: 'var(--cds-spacing-07)' }}>
                              <Button
                                kind="secondary"
                                onClick={() => setSelectedPolicy(null)}
                                style={{ width: '100%' }}
                              >
                                Close
                              </Button>
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