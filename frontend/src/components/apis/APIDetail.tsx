import { Clock, Activity, AlertTriangle, CheckCircle, XCircle } from '../../utils/carbonIcons';
import { Heading, Tag, Tile, Grid, Column, InlineNotification } from '@carbon/react';
import Card from '../common/Card';
import type { API } from '../../types';

/**
 * API Detail Component
 *
 * Displays detailed information about a specific API including:
 * - Basic information and metadata
 * - Endpoints and methods
 * - Current metrics and health status
 * - Authentication configuration
 */

interface APIDetailProps {
  api: API;
  onClose?: () => void;
}

const APIDetail = ({ api, onClose }: APIDetailProps) => {
  // Get health score tag type
  const getHealthTagType = (score: number): 'green' | 'warm-gray' | 'red' => {
    if (score >= 80) return 'green';
    if (score >= 50) return 'warm-gray';
    return 'red';
  };

  // Get health label
  const getHealthLabel = (score: number): string => {
    if (score >= 80) return 'Excellent';
    if (score >= 50) return 'Good';
    return 'Poor';
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle size={20} style={{ color: 'var(--cds-support-success)' }} />;
      case 'inactive': return <Clock size={20} style={{ color: 'var(--cds-icon-secondary)' }} />;
      case 'deprecated': return <AlertTriangle size={20} style={{ color: 'var(--cds-support-warning)' }} />;
      case 'failed': return <XCircle size={20} style={{ color: 'var(--cds-support-error)' }} />;
      default: return <Activity size={20} style={{ color: 'var(--cds-icon-secondary)' }} />;
    }
  };

  // Get method tag type
  const getMethodTagType = (method: string): 'blue' | 'green' | 'warm-gray' | 'red' | 'gray' => {
    switch (method) {
      case 'GET': return 'blue';
      case 'POST': return 'green';
      case 'PUT': return 'warm-gray';
      case 'DELETE': return 'red';
      default: return 'gray';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-07)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)', marginBottom: 'var(--cds-spacing-03)', flexWrap: 'wrap' }}>
            <Heading>{api.name}</Heading>
            {api.version && (
              <Tag type="gray">v{api.version}</Tag>
            )}
          </div>
          <p style={{ color: 'var(--cds-text-secondary)', fontSize: '0.875rem' }}>{api.base_path}</p>
        </div>
      </div>

      {/* Status and Health */}
      <Grid narrow>
        <Column lg={5} md={4} sm={4}>
          <Tile style={{ padding: 'var(--cds-spacing-05)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
              {getStatusIcon(api.status)}
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Status</p>
                <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)', textTransform: 'capitalize' }}>{api.status}</p>
              </div>
            </div>
          </Tile>
        </Column>

        <Column lg={5} md={4} sm={4}>
          <Tile style={{ padding: 'var(--cds-spacing-05)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
              <Tag type={getHealthTagType(api.health_score)} size="md" style={{ fontSize: '1.125rem', fontWeight: 600, padding: 'var(--cds-spacing-04)' }}>
                {api.health_score.toFixed(0)}
              </Tag>
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Health Score</p>
                <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                  {getHealthLabel(api.health_score)}
                </p>
              </div>
            </div>
          </Tile>
        </Column>

        <Column lg={6} md={4} sm={4}>
          <Tile style={{ padding: 'var(--cds-spacing-05)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
              <Activity size={32} style={{ color: 'var(--cds-link-primary)' }} />
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Discovery Method</p>
                <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)', textTransform: 'capitalize' }}>
                  {api.discovery_method.replace('_', ' ')}
                </p>
              </div>
            </div>
          </Tile>
        </Column>
      </Grid>

      {/* Shadow API Warning */}
      {api.is_shadow && (
        <InlineNotification
          kind="warning"
          title="Shadow API Detected"
          subtitle="This API was discovered through traffic analysis and may not be officially documented."
          lowContrast
          hideCloseButton
        />
      )}

      {/* Current Metrics */}
      <Card title="Current Metrics" subtitle="Latest performance measurements">
        <Grid narrow>
          <Column lg={5} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Response Time (P50)</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {api.current_metrics.response_time_p50.toFixed(1)}ms
              </p>
            </div>
          </Column>
          <Column lg={5} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Response Time (P95)</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {api.current_metrics.response_time_p95.toFixed(1)}ms
              </p>
            </div>
          </Column>
          <Column lg={6} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Response Time (P99)</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {api.current_metrics.response_time_p99.toFixed(1)}ms
              </p>
            </div>
          </Column>
          <Column lg={5} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Error Rate</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {(api.current_metrics.error_rate * 100).toFixed(2)}%
              </p>
            </div>
          </Column>
          <Column lg={5} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Throughput</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {api.current_metrics.throughput.toFixed(1)} req/s
              </p>
            </div>
          </Column>
          <Column lg={6} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Availability</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                {api.current_metrics.availability.toFixed(2)}%
              </p>
            </div>
          </Column>
        </Grid>
        <div style={{ marginTop: 'var(--cds-spacing-05)', fontSize: '0.75rem', color: 'var(--cds-text-helper)' }}>
          Last measured: {new Date(api.current_metrics.measured_at).toLocaleString()}
        </div>
      </Card>

      {/* Endpoints */}
      <Card title="Endpoints" subtitle={`${api.endpoints.length} endpoints available`}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-03)' }}>
          {api.endpoints.map((endpoint, index) => (
            <Tile key={index} style={{ padding: 'var(--cds-spacing-04)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
                <Tag type={getMethodTagType(endpoint.method)} size="sm" style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                  {endpoint.method}
                </Tag>
                <code style={{ fontSize: '0.875rem', fontFamily: 'monospace', color: 'var(--cds-text-primary)' }}>{endpoint.path}</code>
              </div>
              {endpoint.description && (
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginTop: 'var(--cds-spacing-02)', marginLeft: 'var(--cds-spacing-09)' }}>{endpoint.description}</p>
              )}
            </Tile>
          ))}
        </div>
      </Card>

      {/* Authentication */}
      <Card title="Authentication" subtitle="Security configuration">
        <div className="space-y-3">
          <div>
            <p className="text-sm text-gray-600">Type</p>
            <p className="text-lg font-semibold text-gray-900 capitalize">
              {api.authentication_type.replace('_', ' ')}
            </p>
          </div>
          {api.authentication_config && Object.keys(api.authentication_config).length > 0 && (
            <div>
              <p className="text-sm text-gray-600 mb-2">Configuration</p>
              <div className="p-3 bg-gray-50 rounded font-mono text-sm">
                {Object.entries(api.authentication_config).map(([key, value]) => (
                  <div key={key} className="flex gap-2">
                    <span className="text-gray-600">{key}:</span>
                    <span className="text-gray-900">
                      {typeof value === 'string' && value.length > 50 ? '***' : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Tags */}
      {api.tags && api.tags.length > 0 && (
        <Card title="Tags" subtitle="API categorization">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--cds-spacing-03)' }}>
            {api.tags.map((tag) => (
              <Tag key={tag} type="blue">{tag}</Tag>
            ))}
          </div>
        </Card>
      )}

      {/* Metadata */}
      <Card title="Metadata" subtitle="Additional information">
        <Grid narrow>
          <Column lg={8} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>API ID</p>
              <p style={{ fontFamily: 'monospace', color: 'var(--cds-text-primary)' }}>{api.id}</p>
            </div>
          </Column>
          <Column lg={8} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Gateway ID</p>
              <p style={{ fontFamily: 'monospace', color: 'var(--cds-text-primary)' }}>{api.gateway_id}</p>
            </div>
          </Column>
          <Column lg={8} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Discovered At</p>
              <p style={{ color: 'var(--cds-text-primary)' }}>{new Date(api.discovered_at).toLocaleString()}</p>
            </div>
          </Column>
          <Column lg={8} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Last Seen At</p>
              <p style={{ color: 'var(--cds-text-primary)' }}>{new Date(api.last_seen_at).toLocaleString()}</p>
            </div>
          </Column>
          <Column lg={8} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Created At</p>
              <p style={{ color: 'var(--cds-text-primary)' }}>{new Date(api.created_at).toLocaleString()}</p>
            </div>
          </Column>
          <Column lg={8} md={4} sm={4}>
            <div style={{ marginBottom: 'var(--cds-spacing-05)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Updated At</p>
              <p style={{ color: 'var(--cds-text-primary)' }}>{new Date(api.updated_at).toLocaleString()}</p>
            </div>
          </Column>
        </Grid>
      </Card>
    </div>
  );
};

export default APIDetail;

// Made with Bob