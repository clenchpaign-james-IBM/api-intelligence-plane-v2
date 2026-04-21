import type { Metric } from '../../types'
import Card from '../common/Card'

interface MetricsChartProps {
  metrics: Metric[]
  onSelectMetric?: (metric: Metric) => void
}

const MetricsChart = ({ metrics, onSelectMetric }: MetricsChartProps) => {
  const maxRequestCount = Math.max(...metrics.map((metric) => metric.request_count), 0)

  return (
    <Card
      title="Metrics Overview"
      subtitle="Click a bucket below to drill down into transactional logs"
    >
      {metrics.length === 0 ? (
        <div className="py-8 text-sm text-gray-500">
          No metrics available for the selected filters
        </div>
      ) : (
        <div className="space-y-3">
          {metrics.map((metric) => {
            const width =
              maxRequestCount > 0
                ? `${Math.max((metric.request_count / maxRequestCount) * 100, 4)}%`
                : '4%'

            return (
              <button
                key={metric.id}
                type="button"
                onClick={() => onSelectMetric?.(metric)}
                className="w-full rounded-md border border-gray-200 p-3 text-left transition hover:border-blue-300 hover:bg-blue-50"
              >
                <div className="mb-2 flex items-center justify-between gap-4">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {new Date(metric.timestamp).toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500">
                      {metric.request_count.toLocaleString()} requests • P95{' '}
                      {metric.response_time_p95.toFixed(1)} ms
                    </div>
                  </div>
                  <div className="text-xs font-medium text-gray-500">
                    {metric.time_bucket}
                  </div>
                </div>
                <div className="h-3 rounded-full bg-gray-100">
                  <div
                    className="h-3 rounded-full bg-blue-600"
                    style={{ width }}
                  />
                </div>
              </button>
            )
          })}
        </div>
      )}
    </Card>
  )
}

export default MetricsChart

// Made with Bob
