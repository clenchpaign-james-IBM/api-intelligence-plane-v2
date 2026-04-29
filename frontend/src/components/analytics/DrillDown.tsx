import { useState } from 'react'
import type { Metric, TransactionalLog } from '../../types'
import Card from '../common/Card'
import Loading from '../common/Loading'

interface DrillDownProps {
  metric: Metric
  logs: TransactionalLog[]
  isLoading?: boolean
  onClose?: () => void
}

const DrillDown = ({ metric, logs, isLoading, onClose }: DrillDownProps) => {
  const [selectedLog, setSelectedLog] = useState<TransactionalLog | null>(null)

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const formatDuration = (ms?: number) => {
    return ms ? `${ms.toFixed(0)}ms` : 'N/A'
  }

  const getStatusBadge = (statusCode?: number) => {
    if (!statusCode) return 'bg-gray-100 text-gray-800'
    if (statusCode >= 200 && statusCode < 300)
      return 'bg-green-100 text-green-800'
    if (statusCode >= 300 && statusCode < 400) return 'bg-blue-100 text-blue-800'
    if (statusCode >= 400 && statusCode < 500)
      return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  const errorRate = metric.failure_count / metric.request_count
  const availability = (metric.success_count / metric.request_count) * 100

  return (
    <Card
      title="Drill-Down: Transactional Logs"
      subtitle={`Showing logs for metric at ${formatTimestamp(metric.timestamp)}`}
    >
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="mb-4 text-sm text-blue-600 hover:text-blue-800"
        >
          ← Back to Metrics
        </button>
      )}

      {/* Metric Summary */}
      <div className="mb-6 grid grid-cols-2 gap-4 rounded-lg bg-gray-50 p-4 md:grid-cols-4">
        <div>
          <div className="text-xs text-gray-500">Total Requests</div>
          <div className="text-lg font-semibold text-gray-900">
            {metric.request_count.toLocaleString()}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500">Error Rate</div>
          <div className="text-lg font-semibold text-gray-900">
            {(errorRate * 100).toFixed(2)}%
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500">P95 Response Time</div>
          <div className="text-lg font-semibold text-gray-900">
            {metric.response_time_p95.toFixed(0)}ms
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500">Availability</div>
          <div className="text-lg font-semibold text-gray-900">
            {availability.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Logs List */}
      {isLoading ? (
        <Loading message="Loading transactional logs..." />
      ) : logs.length === 0 ? (
        <div className="py-8 text-center text-sm text-gray-500">
          No transactional logs found for this metric
        </div>
      ) : (
        <div className="space-y-2">
          <div className="mb-2 text-sm font-medium text-gray-700">
            {logs.length} log{logs.length !== 1 ? 's' : ''} found
          </div>
          {logs.map((log) => (
            <button
              key={log.id}
              type="button"
              onClick={() =>
                setSelectedLog(selectedLog?.id === log.id ? null : log)
              }
              className="w-full rounded-md border border-gray-200 p-3 text-left transition hover:border-blue-300 hover:bg-blue-50"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    <span
                      className={`inline-flex rounded px-2 py-0.5 text-xs font-medium ${getStatusBadge(log.status_code)}`}
                    >
                      {log.status_code || 'N/A'}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {log.method || 'GET'} {log.path || log.resource_path || '/'}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                    <span>⏱ {formatDuration(log.total_time_ms || log.latency_ms)}</span>
                    {log.correlation_id && (
                      <span>🔗 {log.correlation_id.substring(0, 8)}...</span>
                    )}
                    <span>👤 {log.consumer_name || log.consumer_id || 'Unknown'}</span>
                    <span>🕐 {formatTimestamp(log.timestamp)}</span>
                  </div>
                </div>
                <div className="text-xs text-gray-400">
                  {selectedLog?.id === log.id ? '▼' : '▶'}
                </div>
              </div>

              {/* Expanded Details */}
              {selectedLog?.id === log.id && (
                <div className="mt-3 space-y-3 border-t border-gray-200 pt-3">
                  {/* Timing Breakdown */}
                  {(log.latency_ms || log.backend_latency_ms) && (
                    <div>
                      <div className="mb-1 text-xs font-medium text-gray-700">
                        Timing Breakdown
                      </div>
                      <div className="space-y-1 text-xs text-gray-600">
                        {log.backend_latency_ms && (
                          <div className="flex justify-between">
                            <span>Backend Time:</span>
                            <span className="font-medium">
                              {formatDuration(log.backend_latency_ms)}
                            </span>
                          </div>
                        )}
                        <div className="flex justify-between border-t border-gray-200 pt-1">
                          <span>Total Time:</span>
                          <span className="font-medium">
                            {formatDuration(log.total_time_ms || log.latency_ms)}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Request/Response Details */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="mb-1 text-xs font-medium text-gray-700">
                        Request
                      </div>
                      <div className="space-y-1 text-xs text-gray-600">
                        {log.request_size_bytes && (
                          <div>Size: {log.request_size_bytes} bytes</div>
                        )}
                        {log.client_ip && <div>IP: {log.client_ip}</div>}
                      </div>
                    </div>
                    <div>
                      <div className="mb-1 text-xs font-medium text-gray-700">
                        Response
                      </div>
                      <div className="space-y-1 text-xs text-gray-600">
                        {log.response_size_bytes && (
                          <div>Size: {log.response_size_bytes} bytes</div>
                        )}
                        {log.cache_status && <div>Cache: {log.cache_status}</div>}
                      </div>
                    </div>
                  </div>

                  {/* External Calls */}
                  {log.external_calls && log.external_calls.length > 0 && (
                    <div>
                      <div className="mb-1 text-xs font-medium text-gray-700">
                        External Calls ({log.external_calls.length})
                      </div>
                      <div className="space-y-1">
                        {log.external_calls.map((call, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between rounded bg-gray-50 px-2 py-1 text-xs"
                          >
                            <span className="text-gray-600">
                              {call.call_type}: {call.target_service}
                            </span>
                            <span
                              className={
                                call.success ? 'text-green-600' : 'text-red-600'
                              }
                            >
                              {formatDuration(call.duration_ms)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Error Details */}
                  {log.error_message && (
                    <div className="rounded-md bg-red-50 p-2">
                      <div className="mb-1 text-xs font-medium text-red-800">
                        Error Details
                      </div>
                      <div className="text-xs text-red-700">
                        {log.error_origin && <div>Origin: {log.error_origin}</div>}
                        <div>Message: {log.error_message}</div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </Card>
  )
}

export default DrillDown

// Made with Bob