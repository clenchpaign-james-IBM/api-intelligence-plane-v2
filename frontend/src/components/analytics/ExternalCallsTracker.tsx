import type { ExternalCall } from '../../types'
import Card from '../common/Card'

interface ExternalCallsTrackerProps {
  calls: ExternalCall[]
  title?: string
}

const ExternalCallsTracker = ({
  calls,
  title = 'External Service Calls',
}: ExternalCallsTrackerProps) => {
  const formatDuration = (ms: number) => {
    return `${ms.toFixed(0)}ms`
  }

  const getCallTypeColor = (callType: string) => {
    switch (callType) {
      case 'http':
        return 'bg-blue-100 text-blue-800'
      case 'database':
        return 'bg-purple-100 text-purple-800'
      case 'cache':
        return 'bg-green-100 text-green-800'
      case 'messaging':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (success: boolean) => {
    return success ? 'text-green-600' : 'text-red-600'
  }

  const totalDuration = calls.reduce((sum, call) => sum + call.duration_ms, 0)
  const successCount = calls.filter((call) => call.success).length
  const failureCount = calls.length - successCount
  const avgDuration = calls.length > 0 ? totalDuration / calls.length : 0

  // Group calls by service
  const callsByService = calls.reduce(
    (acc, call) => {
      const service = call.target_service
      if (!acc[service]) {
        acc[service] = []
      }
      acc[service].push(call)
      return acc
    },
    {} as Record<string, ExternalCall[]>
  )

  return (
    <Card title={title}>
      {calls.length === 0 ? (
        <div className="py-8 text-center text-sm text-gray-500">
          No external calls recorded
        </div>
      ) : (
        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-4 rounded-lg bg-gray-50 p-4 md:grid-cols-4">
            <div>
              <div className="text-xs text-gray-500">Total Calls</div>
              <div className="text-lg font-semibold text-gray-900">
                {calls.length}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Success Rate</div>
              <div className="text-lg font-semibold text-gray-900">
                {calls.length > 0
                  ? ((successCount / calls.length) * 100).toFixed(1)
                  : 0}
                %
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Avg Duration</div>
              <div className="text-lg font-semibold text-gray-900">
                {formatDuration(avgDuration)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Total Time</div>
              <div className="text-lg font-semibold text-gray-900">
                {formatDuration(totalDuration)}
              </div>
            </div>
          </div>

          {/* Calls by Service */}
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700">
              Calls by Service
            </h3>
            <div className="space-y-2">
              {Object.entries(callsByService).map(([service, serviceCalls]) => {
                const serviceTotal = serviceCalls.reduce(
                  (sum, call) => sum + call.duration_ms,
                  0
                )
                const serviceSuccess = serviceCalls.filter(
                  (call) => call.success
                ).length
                const serviceAvg = serviceTotal / serviceCalls.length

                return (
                  <div
                    key={service}
                    className="rounded-md border border-gray-200 p-3"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          {service}
                        </span>
                        <span className="text-xs text-gray-500">
                          ({serviceCalls.length} call
                          {serviceCalls.length !== 1 ? 's' : ''})
                        </span>
                      </div>
                      <div className="text-sm text-gray-600">
                        {formatDuration(serviceAvg)} avg
                      </div>
                    </div>

                    {/* Individual Calls */}
                    <div className="space-y-1">
                      {serviceCalls.map((call, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between rounded bg-gray-50 px-2 py-1.5 text-xs"
                        >
                          <div className="flex items-center gap-2">
                            <span
                              className={`inline-flex rounded px-1.5 py-0.5 font-medium ${getCallTypeColor(call.call_type)}`}
                            >
                              {call.call_type}
                            </span>
                            {call.target_endpoint && (
                              <span className="text-gray-600">
                                {call.target_endpoint}
                              </span>
                            )}
                            {call.status_code && (
                              <span className="text-gray-500">
                                [{call.status_code}]
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className={`font-medium ${getStatusColor(call.success)}`}
                            >
                              {formatDuration(call.duration_ms)}
                            </span>
                            <span className="text-gray-400">
                              {call.success ? '✓' : '✗'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Service Summary */}
                    <div className="mt-2 flex items-center justify-between border-t border-gray-200 pt-2 text-xs text-gray-600">
                      <span>
                        Success: {serviceSuccess}/{serviceCalls.length}
                      </span>
                      <span>Total: {formatDuration(serviceTotal)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Failed Calls */}
          {failureCount > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-medium text-red-700">
                Failed Calls ({failureCount})
              </h3>
              <div className="space-y-1">
                {calls
                  .filter((call) => !call.success)
                  .map((call, idx) => (
                    <div
                      key={idx}
                      className="rounded-md border border-red-200 bg-red-50 p-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-xs">
                          <span
                            className={`inline-flex rounded px-1.5 py-0.5 font-medium ${getCallTypeColor(call.call_type)}`}
                          >
                            {call.call_type}
                          </span>
                          <span className="font-medium text-gray-900">
                            {call.target_service}
                          </span>
                          {call.target_endpoint && (
                            <span className="text-gray-600">
                              {call.target_endpoint}
                            </span>
                          )}
                        </div>
                        <span className="text-xs font-medium text-red-600">
                          {formatDuration(call.duration_ms)}
                        </span>
                      </div>
                      {call.error_message && (
                        <div className="mt-1 text-xs text-red-700">
                          Error: {call.error_message}
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

export default ExternalCallsTracker

// Made with Bob