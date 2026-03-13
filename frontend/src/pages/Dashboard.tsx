import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Grid, Column, Heading, Tag, Tile, ClickableTile } from '@carbon/react';
import { Activity, AlertTriangle, Server, Zap, Plus } from '../utils/carbonIcons';
import Card from '../components/common/Card';
import Loading from '../components/common/Loading';
import Error from '../components/common/Error';
import AddGatewayForm from '../components/gateways/AddGatewayForm';
import { api } from '../services/api';
import type { DashboardStats, API, Gateway } from '../types';

/**
 * Dashboard Page
 * 
 * Displays overview of the API Intelligence Plane system:
 * - Key metrics and statistics
 * - API health overview
 * - Gateway status
 * - Recent alerts and recommendations
 */
const Dashboard = () => {
  const [showAddGatewayForm, setShowAddGatewayForm] = useState(false);

  // Fetch dashboard data
  const { data: apis, isLoading: apisLoading, error: apisError } = useQuery({
    queryKey: ['apis'],
    queryFn: () => api.apis.list(),
  });

  const { data: gateways, isLoading: gatewaysLoading, error: gatewaysError, refetch: refetchGateways } = useQuery({
    queryKey: ['gateways'],
    queryFn: () => api.gateways.list(),
  });

  // Calculate dashboard statistics
  const stats: DashboardStats = {
    total_apis: apis?.items?.length || 0,
    active_apis: apis?.items?.filter((a: API) => a.status === 'active').length || 0,
    shadow_apis: apis?.items?.filter((a: API) => a.is_shadow).length || 0,
    total_gateways: gateways?.items?.length || 0,
    active_gateways: gateways?.items?.filter((g: Gateway) => g.status === 'connected').length || 0,
    avg_health_score: apis?.items?.length
      ? apis.items.reduce((sum: number, a: API) => sum + a.health_score, 0) / apis.items.length
      : 0,
    avg_response_time: apis?.items?.length
      ? apis.items.reduce((sum: number, a: API) => sum + a.current_metrics.response_time_p95, 0) / apis.items.length
      : 0,
    total_requests_24h: 0, // Would come from metrics aggregation
    error_rate_24h: 0, // Would come from metrics aggregation
    critical_vulnerabilities: 0, // Would come from security scan
    high_priority_recommendations: 0, // Would come from recommendations
  };

  // Loading state
  if (apisLoading || gatewaysLoading) {
    return (
      <div style={{ padding: 'var(--cds-spacing-06)' }}>
        <Loading message="Loading dashboard..." />
      </div>
    );
  }

  // Error state
  if (apisError || gatewaysError) {
    return (
      <div style={{ padding: 'var(--cds-spacing-06)' }}>
        <Error
          message="Failed to load dashboard data"
          details={(apisError || gatewaysError) as Error}
        />
      </div>
    );
  }

  return (
    <div style={{ padding: 'var(--cds-spacing-06)' }}>
      {/* Page Header */}
      <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
        <Heading style={{ marginBottom: 'var(--cds-spacing-03)' }}>Dashboard</Heading>
        <p style={{ color: 'var(--cds-text-secondary)', fontSize: '0.875rem' }}>
          Overview of your API infrastructure and health metrics
        </p>
      </div>

      {/* Key Metrics Grid */}
      <Grid narrow style={{ marginBottom: 'var(--cds-spacing-07)' }}>
        <Column lg={4} md={4} sm={4}>
          <Tile style={{ padding: 'var(--cds-spacing-05)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-03)' }}>Total APIs</p>
                <p style={{ fontSize: '2rem', fontWeight: 600, color: 'var(--cds-text-primary)', lineHeight: 1, marginBottom: 'var(--cds-spacing-02)' }}>{stats.total_apis}</p>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>
                  {stats.active_apis} active
                </p>
              </div>
              <div style={{ padding: 'var(--cds-spacing-04)', backgroundColor: 'var(--cds-layer-accent)', borderRadius: 'var(--cds-spacing-02)' }}>
                <Server size={32} />
              </div>
            </div>
          </Tile>
        </Column>

        <Column lg={4} md={4} sm={4}>
          <Tile style={{ padding: 'var(--cds-spacing-05)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-03)' }}>Avg Health Score</p>
                <p style={{ fontSize: '2rem', fontWeight: 600, color: 'var(--cds-text-primary)', lineHeight: 1, marginBottom: 'var(--cds-spacing-02)' }}>
                  {stats.avg_health_score.toFixed(1)}
                </p>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>
                  out of 100
                </p>
              </div>
              <div style={{ padding: 'var(--cds-spacing-04)', backgroundColor: 'var(--cds-layer-accent)', borderRadius: 'var(--cds-spacing-02)' }}>
                <Activity size={32} />
              </div>
            </div>
          </Tile>
        </Column>

        <Column lg={4} md={4} sm={4}>
          <Tile style={{ padding: 'var(--cds-spacing-05)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-03)' }}>Shadow APIs</p>
                <p style={{ fontSize: '2rem', fontWeight: 600, color: 'var(--cds-text-primary)', lineHeight: 1, marginBottom: 'var(--cds-spacing-02)' }}>{stats.shadow_apis}</p>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>
                  {stats.shadow_apis > 0 ? 'Needs attention' : 'All documented'}
                </p>
              </div>
              <div style={{ padding: 'var(--cds-spacing-04)', backgroundColor: 'var(--cds-layer-accent)', borderRadius: 'var(--cds-spacing-02)' }}>
                <AlertTriangle size={32} />
              </div>
            </div>
          </Tile>
        </Column>

        <Column lg={4} md={4} sm={4}>
          <Tile style={{ padding: 'var(--cds-spacing-05)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-03)' }}>Active Gateways</p>
                <p style={{ fontSize: '2rem', fontWeight: 600, color: 'var(--cds-text-primary)', lineHeight: 1, marginBottom: 'var(--cds-spacing-02)' }}>{stats.active_gateways}</p>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>
                  of {stats.total_gateways} total
                </p>
              </div>
              <div style={{ padding: 'var(--cds-spacing-04)', backgroundColor: 'var(--cds-layer-accent)', borderRadius: 'var(--cds-spacing-02)' }}>
                <Zap size={32} />
              </div>
            </div>
          </Tile>
        </Column>
      </Grid>

      {/* API Health Overview */}
      <Grid narrow style={{ marginBottom: 'var(--cds-spacing-07)' }}>
        {/* Top APIs by Health Score */}
        <Column lg={8} md={4} sm={4}>
          <Card title="Top Performing APIs" subtitle="Highest health scores">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-06)' }}>
              {apis?.items
                ?.sort((a: API, b: API) => b.health_score - a.health_score)
                .slice(0, 5)
                .map((api: API) => (
                  <Tile
                    key={api.id}
                    style={{
                      padding: 'var(--cds-spacing-05)',
                      border: '1px solid var(--cds-border-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--cds-spacing-04)' }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <p style={{ fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-02)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{api.name}</p>
                        <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{api.base_path}</p>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)', flexShrink: 0 }}>
                        <div style={{ textAlign: 'right' }}>
                          <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)', lineHeight: 1, marginBottom: 'var(--cds-spacing-02)' }}>
                            {api.health_score.toFixed(1)}
                          </p>
                          <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>Health Score</p>
                        </div>
                        <Tag
                          type={api.health_score >= 80 ? 'green' : api.health_score >= 50 ? 'warm-gray' : 'red'}
                          size="md"
                        >
                          {api.health_score >= 80 ? 'Healthy' : api.health_score >= 50 ? 'Fair' : 'Poor'}
                        </Tag>
                      </div>
                    </div>
                  </Tile>
                ))}
              {(!apis?.items || apis.items.length === 0) && (
                <p style={{ textAlign: 'center', color: 'var(--cds-text-secondary)', padding: 'var(--cds-spacing-07)' }}>No APIs found</p>
              )}
            </div>
          </Card>
        </Column>

        {/* APIs Needing Attention */}
        <Column lg={8} md={4} sm={4}>
          <Card title="APIs Needing Attention" subtitle="Low health scores or issues">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-06)' }}>
              {apis?.items
                ?.filter((a: API) => a.health_score < 70 || a.status === 'failed')
                .sort((a: API, b: API) => a.health_score - b.health_score)
                .slice(0, 5)
                .map((api: API) => (
                  <Tile
                    key={api.id}
                    style={{
                      padding: 'var(--cds-spacing-05)',
                      border: '1px solid var(--cds-border-subtle)',
                      borderLeft: '4px solid var(--cds-support-error)',
                      backgroundColor: 'var(--cds-layer-01)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--cds-spacing-04)' }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <p style={{ fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-02)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{api.name}</p>
                        <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{api.base_path}</p>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)', flexShrink: 0 }}>
                        <div style={{ textAlign: 'right' }}>
                          <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-support-error)', lineHeight: 1, marginBottom: 'var(--cds-spacing-02)' }}>
                            {api.health_score.toFixed(1)}
                          </p>
                          <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>Health Score</p>
                        </div>
                        <AlertTriangle size={24} style={{ color: 'var(--cds-support-error)' }} />
                      </div>
                    </div>
                  </Tile>
                ))}
              {(!apis?.items || apis.items.filter((a: API) => a.health_score < 70).length === 0) && (
                <div style={{ textAlign: 'center', padding: 'var(--cds-spacing-07)' }}>
                  <p style={{ color: 'var(--cds-support-success)', fontWeight: 500, marginBottom: 'var(--cds-spacing-02)' }}>
                    All APIs are performing well! 🎉
                  </p>
                  <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>
                    No APIs require immediate attention
                  </p>
                </div>
              )}
            </div>
          </Card>
        </Column>
      </Grid>

      {/* Gateway Status */}
      <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
        <Card title="Gateway Status" subtitle="Connected API gateways">
          <Grid narrow>
            {gateways?.items?.map((gateway: Gateway) => (
              <Column key={gateway.id} lg={5} md={4} sm={4} style={{ marginBottom: 'var(--cds-spacing-06)' }}>
                <Tile
                  style={{
                    padding: 'var(--cds-spacing-05)',
                    border: '1px solid var(--cds-border-subtle)',
                    height: '100%',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 'var(--cds-spacing-04)', gap: 'var(--cds-spacing-03)' }}>
                    <h4 style={{ fontWeight: 600, color: 'var(--cds-text-primary)', fontSize: '1rem', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{gateway.name}</h4>
                    <Tag
                      type={gateway.status === 'connected' ? 'green' : gateway.status === 'disconnected' ? 'gray' : 'red'}
                      size="md"
                    >
                      {gateway.status}
                    </Tag>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-03)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
                      <Server size={16} style={{ color: 'var(--cds-icon-secondary)', flexShrink: 0 }} />
                      <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', fontWeight: 500 }}>{gateway.vendor}</p>
                    </div>
                    <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', paddingLeft: 'calc(16px + var(--cds-spacing-03))' }}>
                      {gateway.connection_url}
                    </p>
                    {gateway.last_connected_at && (
                      <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-helper)', marginTop: 'var(--cds-spacing-02)', paddingLeft: 'calc(16px + var(--cds-spacing-03))' }}>
                        Last connected: {new Date(gateway.last_connected_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                </Tile>
              </Column>
            ))}
            {(!gateways?.items || gateways.items.length === 0) && (
              <Column lg={16} md={8} sm={4}>
                <div style={{ textAlign: 'center', padding: 'var(--cds-spacing-09)' }}>
                  <Server size={48} style={{ color: 'var(--cds-icon-disabled)', margin: '0 auto var(--cds-spacing-05)' }} />
                  <p style={{ color: 'var(--cds-text-secondary)', fontWeight: 500, marginBottom: 'var(--cds-spacing-02)' }}>
                    No gateways configured
                  </p>
                  <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-helper)' }}>
                    Add a gateway to start discovering APIs
                  </p>
                </div>
              </Column>
            )}
          </Grid>
        </Card>
      </div>

      {/* Quick Actions */}
      <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
        <Heading style={{ marginBottom: 'var(--cds-spacing-05)', fontSize: '1.125rem' }}>Quick Actions</Heading>
        <Grid narrow>
          <Column lg={5} md={4} sm={4}>
            <ClickableTile onClick={() => setShowAddGatewayForm(true)}>
              <div style={{ textAlign: 'center', padding: 'var(--cds-spacing-04)' }}>
                <Plus size={32} style={{ margin: '0 auto var(--cds-spacing-04)', color: 'var(--cds-icon-secondary)' }} />
                <p style={{ fontWeight: 500, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-02)' }}>Add Gateway</p>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Connect a new API gateway</p>
              </div>
            </ClickableTile>
          </Column>
          <Column lg={5} md={4} sm={4}>
            <Link to="/apis" style={{ textDecoration: 'none' }}>
              <ClickableTile>
                <div style={{ textAlign: 'center', padding: 'var(--cds-spacing-04)' }}>
                  <Server size={32} style={{ margin: '0 auto var(--cds-spacing-04)', color: 'var(--cds-icon-secondary)' }} />
                  <p style={{ fontWeight: 500, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-02)' }}>View All APIs</p>
                  <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Browse API inventory</p>
                </div>
              </ClickableTile>
            </Link>
          </Column>
          <Column lg={5} md={4} sm={4}>
            <Link to="/predictions" style={{ textDecoration: 'none' }}>
              <ClickableTile>
                <div style={{ textAlign: 'center', padding: 'var(--cds-spacing-04)' }}>
                  <Activity size={32} style={{ margin: '0 auto var(--cds-spacing-04)', color: 'var(--cds-icon-secondary)' }} />
                  <p style={{ fontWeight: 500, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-02)' }}>View Predictions</p>
                  <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Analyze predictions</p>
                </div>
              </ClickableTile>
            </Link>
          </Column>
        </Grid>
      </div>

      {/* Add Gateway Modal */}
      {showAddGatewayForm && (
        <AddGatewayForm
          onClose={() => setShowAddGatewayForm(false)}
          onSuccess={() => {
            setShowAddGatewayForm(false);
            refetchGateways();
          }}
        />
      )}
    </div>
  );
};

export default Dashboard;

// Made with Bob