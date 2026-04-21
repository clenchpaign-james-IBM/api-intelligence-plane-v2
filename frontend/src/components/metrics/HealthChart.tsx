import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Card from '../common/Card';
import type { Metric } from '../../types';

/**
 * Health Metrics Chart Component
 * 
 * Displays time-series health metrics using Recharts:
 * - Response time (P50, P95, P99)
 * - Error rate
 * - Throughput
 * - Availability
 */

type HealthMetricKey = 'response_time' | 'error_rate' | 'throughput' | 'availability';

interface HealthChartProps {
  data: Metric[];
  title?: string;
  subtitle?: string;
  metrics?: HealthMetricKey[];
  height?: number;
  timeBucket?: string;
}

const HealthChart = ({
  data,
  title = 'Health Metrics',
  subtitle = 'Time-series performance data',
  metrics = ['response_time', 'error_rate'],
  height = 300,
  timeBucket,
}: HealthChartProps) => {
  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };

  const subtitleWithBucket = timeBucket ? `${subtitle} • Bucket: ${timeBucket}` : subtitle;

  // Format data for chart
  const chartData = data.map((point) => {
    const totalRequests = point.request_count ?? 0
    const errorCount = (point.status_4xx_count ?? 0) + (point.status_5xx_count ?? 0)
    const successCount = point.success_count ?? Math.max(totalRequests - errorCount, 0)

    return {
      timestamp: formatTimestamp(point.timestamp),
      fullTimestamp: point.timestamp,
      responseTimeP50: point.response_time_p50 ?? point.response_time_avg ?? 0,
      responseTimeP95: point.response_time_p95 ?? point.response_time_avg ?? 0,
      responseTimeP99: point.response_time_p99 ?? point.response_time_avg ?? 0,
      errorRate: totalRequests > 0 ? (errorCount / totalRequests) * 100 : 0,
      throughput: point.throughput ?? 0,
      availability: totalRequests > 0 ? (successCount / totalRequests) * 100 : 100,
    };
  });

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 mb-2">
            {new Date(data.fullTimestamp).toLocaleString()}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              <span className="font-medium">{entry.name}:</span>{' '}
              {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
              {entry.name.includes('Rate') ? '%' : entry.name.includes('Time') ? 'ms' : ''}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (!data || data.length === 0) {
    return (
      <Card title={title} subtitle={subtitleWithBucket}>
        <div className="flex items-center justify-center h-64 text-gray-500">
          No metrics data available
        </div>
      </Card>
    );
  }

  return (
    <Card title={title} subtitle={subtitleWithBucket}>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="timestamp" 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ fontSize: '12px' }}
            iconType="line"
          />
          
          {/* Response Time Lines */}
          {metrics.includes('response_time') && (
            <>
              <Line
                type="monotone"
                dataKey="responseTimeP50"
                name="Response Time P50"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="responseTimeP95"
                name="Response Time P95"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="responseTimeP99"
                name="Response Time P99"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </>
          )}

          {/* Error Rate Line */}
          {metrics.includes('error_rate') && (
            <Line
              type="monotone"
              dataKey="errorRate"
              name="Error Rate"
              stroke="#dc2626"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          )}

          {/* Throughput Line */}
          {metrics.includes('throughput') && (
            <Line
              type="monotone"
              dataKey="throughput"
              name="Throughput (req/s)"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          )}

          {/* Availability Line */}
          {metrics.includes('availability') && (
            <Line
              type="monotone"
              dataKey="availability"
              name="Availability"
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* Summary Statistics */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
        {metrics.includes('response_time') && (
          <div>
            <p className="text-xs text-gray-600">Avg Response Time (P95)</p>
            <p className="text-lg font-semibold text-gray-900">
              {(chartData.reduce((sum, d) => sum + d.responseTimeP95, 0) / chartData.length).toFixed(1)}ms
            </p>
          </div>
        )}
        {metrics.includes('error_rate') && (
          <div>
            <p className="text-xs text-gray-600">Avg Error Rate</p>
            <p className="text-lg font-semibold text-gray-900">
              {(chartData.reduce((sum, d) => sum + d.errorRate, 0) / chartData.length).toFixed(2)}%
            </p>
          </div>
        )}
        {metrics.includes('throughput') && (
          <div>
            <p className="text-xs text-gray-600">Avg Throughput</p>
            <p className="text-lg font-semibold text-gray-900">
              {(chartData.reduce((sum, d) => sum + d.throughput, 0) / chartData.length).toFixed(1)} req/s
            </p>
          </div>
        )}
        {metrics.includes('availability') && (
          <div>
            <p className="text-xs text-gray-600">Avg Availability</p>
            <p className="text-lg font-semibold text-gray-900">
              {(chartData.reduce((sum, d) => sum + d.availability, 0) / chartData.length).toFixed(2)}%
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default HealthChart;

// Made with Bob