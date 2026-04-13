import Table from '../common/Table'
import type { TransactionalLog } from '../../types'

interface TransactionalLogViewerProps {
  logs: TransactionalLog[]
  loading?: boolean
}

const TransactionalLogViewer = ({
  logs,
  loading = false,
}: TransactionalLogViewerProps) => {
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
          key: 'method',
          header: 'Method',
          render: (value) => <span className="font-medium">{value || '—'}</span>,
        },
        {
          key: 'path',
          header: 'Path',
          render: (value) => (
            <span className="font-mono text-xs">{value || '—'}</span>
          ),
        },
        {
          key: 'status_code',
          header: 'Status',
          render: (value) => value ?? '—',
        },
        {
          key: 'latency_ms',
          header: 'Latency',
          render: (value) =>
            typeof value === 'number' ? `${value.toFixed(1)} ms` : '—',
        },
        {
          key: 'consumer_name',
          header: 'Consumer',
          render: (value) => value || '—',
        },
      ]}
      data={logs}
      keyExtractor={(log) => log.id}
      loading={loading}
      emptyMessage="No transactional logs found for the current drill-down"
    />
  )
}

export default TransactionalLogViewer

// Made with Bob
