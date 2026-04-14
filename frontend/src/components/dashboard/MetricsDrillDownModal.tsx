import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, TrendingUp, TrendingDown, Activity, Clock } from 'lucide-react';
import { metricsService } from '../../services/metrics';
import Loading from '../common/Loading';
import Error from '../common/Error';

interface MetricsDrillDownModalProps {
  apiId: string;
  apiName: string;
  onClose: () => void;
}

/**
 * Metrics Drill-Down Modal
 * 
 * Displays detailed metrics for a specific API including:
 * - Time-series data
 * - Response time percentiles
 * - Error rates
 * - Throughput
 */
const MetricsDrillDownModal = ({ apiId, apiName, onClose }: MetricsDrillDownModalProps) => {
  const [timeBucket, setTimeBucket] = useState<'1m' | '5m' | '1h' | '1d'>('5m');

  // Fetch detailed metrics
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['api-metrics-detail', apiId, timeBucket],
    queryFn: () => metricsService.getMetrics(apiId, { time_bucket: timeBucket }),
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{apiName}</h2>
            <p className="text-sm text-gray-600 mt-1">Detailed Metrics</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Time Bucket Selector */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Granularity:</span>
            <div className="flex gap-2">
              {(['1m', '5m', '1h', '1d'] as const).map((bucket) => (
                <button
                  key={bucket}
                  onClick={() => setTimeBucket(bucket)}
                  className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                    timeBucket === bucket
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                  }`}
                >
                  {bucket}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading && <Loading message="Loading metrics..." />}
          
          {error && (
            <Error
              message="Failed to load metrics"
              onRetry={() => window.location.reload()}
            />
          )}

          {metrics && (
            <div className="space-y-6">
              {/* Aggregated Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-blue-900">Avg Response Time</span>
                    <Activity className="w-4 h-4 text-blue-600" />
                  </div>
                  <p className="text-2xl font-bold text-blue-900 mt-2">
                    {metrics.aggregated.avg_response_time.toFixed(0)}ms
                  </p>
                  <p className="text-xs text-blue-700 mt-1">
                    P95: {metrics.aggregated.p95_response_time.toFixed(0)}ms
                  </p>
                </div>

                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-green-900">Success Rate</span>
                    <TrendingUp className="w-4 h-4 text-green-600" />
                  </div>
                  <p className="text-2xl font-bold text-green-900 mt-2">
                    {metrics.aggregated.success_rate.toFixed(1)}%
                  </p>
                  <p className="text-xs text-green-700 mt-1">
                    {metrics.aggregated.total_requests} requests
                  </p>
                </div>

                <div className={`p-4 rounded-lg ${
                  metrics.aggregated.failure_rate > 5 ? 'bg-red-50' : 'bg-gray-50'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className={`text-sm font-medium ${
                      metrics.aggregated.failure_rate > 5 ? 'text-red-900' : 'text-gray-900'
                    }`}>
                      Error Rate
                    </span>
                    <TrendingDown className={`w-4 h-4 ${
                      metrics.aggregated.failure_rate > 5 ? 'text-red-600' : 'text-gray-600'
                    }`} />
                  </div>
                  <p className={`text-2xl font-bold mt-2 ${
                    metrics.aggregated.failure_rate > 5 ? 'text-red-900' : 'text-gray-900'
                  }`}>
                    {metrics.aggregated.failure_rate.toFixed(1)}%
                  </p>
                </div>
              </div>

              {/* Time Series Data */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Time Series Data</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {metrics.time_series.slice(0, 20).map((point, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
                    >
                      <span className="text-sm text-gray-600">
                        {new Date(point.timestamp).toLocaleString()}
                      </span>
                      <div className="flex gap-4 text-sm">
                        <span className="text-gray-900">
                          {point.request_count} req
                        </span>
                        <span className="text-blue-600">
                          {point.response_time_avg?.toFixed(0)}ms
                        </span>
                        <span className={point.failure_count > 0 ? 'text-red-600' : 'text-green-600'}>
                          {point.failure_count} errors
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Status Breakdown */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">HTTP Status Breakdown</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-900">{metrics.status_breakdown['2xx']}</p>
                    <p className="text-sm text-green-700 mt-1">2xx Success</p>
                  </div>
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-900">{metrics.status_breakdown['3xx']}</p>
                    <p className="text-sm text-blue-700 mt-1">3xx Redirect</p>
                  </div>
                  <div className="text-center p-3 bg-yellow-50 rounded-lg">
                    <p className="text-2xl font-bold text-yellow-900">{metrics.status_breakdown['4xx']}</p>
                    <p className="text-sm text-yellow-700 mt-1">4xx Client Error</p>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded-lg">
                    <p className="text-2xl font-bold text-red-900">{metrics.status_breakdown['5xx']}</p>
                    <p className="text-sm text-red-700 mt-1">5xx Server Error</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default MetricsDrillDownModal;

// Made with Bob