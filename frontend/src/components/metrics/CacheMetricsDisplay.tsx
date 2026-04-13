import Card from '../common/Card'
import type { Metric } from '../../types'

interface CacheMetricsDisplayProps {
  metric?: Metric | null
  title?: string
  subtitle?: string
}

const percentage = (value?: number) => `${(value ?? 0).toFixed(1)}%`

const CacheMetricsDisplay = ({
  metric,
  title = 'Cache Metrics',
  subtitle = 'Cache efficiency derived from time-bucketed metrics',
}: CacheMetricsDisplayProps) => {
  if (!metric) {
    return (
      <Card title={title} subtitle={subtitle}>
        <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-sm text-gray-600">
          No cache metrics available for the selected API and time bucket.
        </div>
      </Card>
    )
  }

  const totalCacheEvents =
    (metric.cache_hit_count ?? 0) +
    (metric.cache_miss_count ?? 0) +
    (metric.cache_bypass_count ?? 0)

  return (
    <Card title={title} subtitle={subtitle}>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="rounded-lg bg-green-50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-green-700">Hit Rate</p>
          <p className="mt-2 text-2xl font-bold text-green-900">{percentage(metric.cache_hit_rate)}</p>
        </div>

        <div className="rounded-lg bg-blue-50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-blue-700">Cache Hits</p>
          <p className="mt-2 text-2xl font-bold text-blue-900">{metric.cache_hit_count ?? 0}</p>
        </div>

        <div className="rounded-lg bg-amber-50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-amber-700">Cache Misses</p>
          <p className="mt-2 text-2xl font-bold text-amber-900">{metric.cache_miss_count ?? 0}</p>
        </div>

        <div className="rounded-lg bg-gray-50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-gray-700">Bypasses</p>
          <p className="mt-2 text-2xl font-bold text-gray-900">{metric.cache_bypass_count ?? 0}</p>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
        <div className="flex flex-col gap-2 text-sm text-gray-700 md:flex-row md:items-center md:justify-between">
          <span>Total cache events: {totalCacheEvents}</span>
          <span>Bucket: {metric.time_bucket}</span>
          <span>Timestamp: {new Date(metric.timestamp).toLocaleString()}</span>
        </div>
      </div>
    </Card>
  )
}

export default CacheMetricsDisplay

// Made with Bob
