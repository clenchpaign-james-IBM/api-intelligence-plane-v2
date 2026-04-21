import Table from '../common/Table'
import type { Metric } from '../../types'

interface MetricsTableProps {
  metrics: Metric[]
  loading?: boolean
  onSelectMetric?: (metric: Metric) => void
}

const formatNumber = (value?: number) =>
  typeof value === 'number' ? value.toLocaleString() : '—'

const formatLatency = (value?: number) =>
  typeof value === 'number' ? `${value.toFixed(1)} ms` : '—'

const MetricsTable = ({
  metrics,
  loading = false,
  onSelectMetric,
}: MetricsTableProps) => {
  return (
    <Table
      columns={[
        {
          key: 'timestamp',
          header: 'Timestamp',
          render: (value) => (
            <span>{value ? new Date(value).toLocaleString() : '—'}</span>
          ),
        },
        {
          key: 'request_count',
          header: 'Requests',
          render: (value) => formatNumber(value),
        },
        {
          key: 'success_count',
          header: 'Success',
          render: (value) => formatNumber(value),
        },
        {
          key: 'failure_count',
          header: 'Failures',
          render: (value) => formatNumber(value),
        },
        {
          key: 'response_time_p95',
          header: 'P95',
          render: (value) => formatLatency(value),
        },
        {
          key: 'cache_hit_rate',
          header: 'Cache Hit Rate',
          render: (value) =>
            typeof value === 'number' ? `${value.toFixed(1)}%` : '—',
        },
      ]}
      data={metrics}
      keyExtractor={(metric) => metric.id}
      onRowClick={onSelectMetric}
      loading={loading}
      emptyMessage="No analytics metrics found for the selected filters"
    />
  )
}

export default MetricsTable

// Made with Bob
