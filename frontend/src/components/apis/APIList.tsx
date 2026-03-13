import { Search, Filter, WarningAltFilled } from '../../utils/carbonIcons';
import { useState } from 'react';
import { Search as CarbonSearch, Select, SelectItem, Tag, Tile, ClickableTile } from '@carbon/react';
import Loading from '../common/Loading';
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

  // Get health score tag type
  const getHealthTagType = (score: number): 'green' | 'warm-gray' | 'red' => {
    if (score >= 80) return 'green';
    if (score >= 50) return 'warm-gray';
    return 'red';
  };

  // Get status tag type
  const getStatusTagType = (status: string): 'green' | 'gray' | 'warm-gray' | 'red' => {
    switch (status) {
      case 'active': return 'green';
      case 'inactive': return 'gray';
      case 'deprecated': return 'warm-gray';
      case 'failed': return 'red';
      default: return 'gray';
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--cds-spacing-09)' }}>
        <Loading />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-07)' }}>
      {/* Search and Filters */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-06)' }}>
        <div style={{ display: 'flex', gap: 'var(--cds-spacing-04)', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 'var(--cds-spacing-05)' }}>
          {/* Search */}
          <div style={{ flex: 1, minWidth: '300px' }}>
            <CarbonSearch
              id="api-search"
              labelText="Search"
              placeholder="Search APIs by name, path, or tags..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="lg"
            />
          </div>

          {/* Status Filter */}
          <div style={{ minWidth: '180px' }}>
            <Select
              id="status-filter"
              labelText="Status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              size="lg"
            >
              <SelectItem value="all" text="All Status" />
              <SelectItem value="active" text="Active" />
              <SelectItem value="inactive" text="Inactive" />
              <SelectItem value="deprecated" text="Deprecated" />
              <SelectItem value="failed" text="Failed" />
            </Select>
          </div>

          {/* Shadow Filter */}
          <div style={{ minWidth: '180px' }}>
            <Select
              id="shadow-filter"
              labelText="API Type"
              value={shadowFilter.toString()}
              onChange={(e) => setShadowFilter(e.target.value === 'all' ? 'all' : e.target.value === 'true')}
              size="lg"
            >
              <SelectItem value="all" text="All APIs" />
              <SelectItem value="false" text="Documented" />
              <SelectItem value="true" text="Shadow APIs" />
            </Select>
          </div>
        </div>

        {/* Results Count */}
        <div style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', fontWeight: 500 }}>
          Showing {filteredAPIs.length} of {apis.length} APIs
        </div>
      </div>

      {/* API List */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {filteredAPIs.length === 0 ? (
          <Tile style={{ padding: 'var(--cds-spacing-09)', textAlign: 'center' }}>
            <WarningAltFilled size={48} style={{ margin: '0 auto var(--cds-spacing-05)', color: 'var(--cds-icon-disabled)' }} />
            <p style={{ color: 'var(--cds-text-secondary)' }}>No APIs found matching your criteria</p>
          </Tile>
        ) : (
          filteredAPIs.map((api, index) => {
            const TileComponent = onSelectAPI ? ClickableTile : Tile;
            return (
              <TileComponent
                key={api.id}
                onClick={() => onSelectAPI?.(api)}
                style={{
                  padding: 'var(--cds-spacing-06)',
                  border: '1px solid var(--cds-border-subtle)',
                  borderLeft: api.is_shadow ? '4px solid var(--cds-support-warning)' : '1px solid var(--cds-border-subtle)',
                  marginBottom: index < filteredAPIs.length - 1 ? 'var(--cds-spacing-07)' : 0
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--cds-spacing-05)' }}>
                  {/* API Info */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)', marginBottom: 'var(--cds-spacing-04)', flexWrap: 'wrap' }}>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--cds-text-primary)', margin: 0 }}>{api.name}</h3>
                      {api.version && (
                        <Tag type="gray" size="sm">v{api.version}</Tag>
                      )}
                      <Tag type={getStatusTagType(api.status)} size="sm">
                        {api.status}
                      </Tag>
                      {api.is_shadow && (
                        <Tag type="warm-gray" size="sm">Shadow API</Tag>
                      )}
                    </div>
                    
                    <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-04)', fontFamily: 'monospace' }}>{api.base_path}</p>
                    
                    {/* Tags */}
                    {api.tags && api.tags.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--cds-spacing-03)', marginBottom: 'var(--cds-spacing-04)' }}>
                        {api.tags.slice(0, 3).map((tag) => (
                          <Tag key={tag} type="blue" size="sm">{tag}</Tag>
                        ))}
                        {api.tags.length > 3 && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)', alignSelf: 'center' }}>
                            +{api.tags.length - 3} more
                          </span>
                        )}
                      </div>
                    )}

                    {/* Metrics */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--cds-spacing-06)', fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>
                      <span>
                        <span style={{ fontWeight: 500 }}>Endpoints:</span> {api.endpoints.length}
                      </span>
                      <span>
                        <span style={{ fontWeight: 500 }}>Methods:</span> {api.methods.join(', ')}
                      </span>
                      <span>
                        <span style={{ fontWeight: 500 }}>Auth:</span> {api.authentication_type}
                      </span>
                      <span>
                        <span style={{ fontWeight: 500 }}>P95:</span> {api.current_metrics.response_time_p95.toFixed(1)}ms
                      </span>
                      <span>
                        <span style={{ fontWeight: 500 }}>Error Rate:</span> {(api.current_metrics.error_rate * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>

                  {/* Health Score */}
                  <div style={{ textAlign: 'center', minWidth: '90px', flexShrink: 0 }}>
                    <Tag type={getHealthTagType(api.health_score)} size="md" style={{ fontSize: '1.25rem', fontWeight: 600, padding: 'var(--cds-spacing-05)', display: 'block' }}>
                      {api.health_score.toFixed(0)}
                    </Tag>
                    <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)', marginTop: 'var(--cds-spacing-03)', fontWeight: 500 }}>Health Score</p>
                  </div>
                </div>
              </TileComponent>
            );
          })
        )}
      </div>
    </div>
  );
};

export default APIList;

// Made with Bob