import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Activity, AlertTriangle } from 'lucide-react';
import type { RateLimitEffectivenessResponse } from '../../types';

interface RateLimitChartProps {
  effectiveness: RateLimitEffectivenessResponse;
}

/**
 * RateLimitChart Component
 * 
 * Visualizes rate limit policy effectiveness with:
 * - Effectiveness score gauge
 * - Metrics breakdown (error rate, response time, throttled requests)
 * - Recommendations list
 * - Analysis period display
 */
const RateLimitChart = ({ effectiveness }: RateLimitChartProps) => {
  // Prepare data for metrics chart
  const metricsData = [
    {
      name: 'Error Rate',
      value: effectiveness.metrics.error_rate * 100,
      color: '#ef4444',
    },
    {
      name: 'Throttled %',
      value: (effectiveness.metrics.throttled_requests / effectiveness.metrics.total_requests) * 100,
      color: '#f59e0b',
    },
  ];

  // Prepare data for response time visualization
  const responseTimeData = [
    {
      name: 'Avg Response Time',
      value: effectiveness.metrics.avg_response_time,
      target: 200, // Target response time in ms
    },
  ];

  // Calculate effectiveness color
  const getEffectivenessColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Calculate effectiveness background color
  const getEffectivenessBgColor = (score: number) => {
    if (score >= 0.8) return 'from-green-500 to-emerald-500';
    if (score >= 0.6) return 'from-yellow-500 to-orange-500';
    return 'from-red-500 to-rose-500';
  };

  const effectivenessColor = getEffectivenessColor(effectiveness.effectiveness_score);
  const effectivenessBgColor = getEffectivenessBgColor(effectiveness.effectiveness_score);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-6">Rate Limit Effectiveness Analysis</h3>

      {/* Effectiveness Score Gauge */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-700">Overall Effectiveness</span>
          <span className={`text-3xl font-bold ${effectivenessColor}`}>
            {(effectiveness.effectiveness_score * 100).toFixed(0)}%
          </span>
        </div>
        <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full bg-gradient-to-r ${effectivenessBgColor} transition-all duration-500`}
            style={{ width: `${effectiveness.effectiveness_score * 100}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Poor</span>
          <span>Fair</span>
          <span>Good</span>
          <span>Excellent</span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-red-900">Error Rate</span>
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <p className="text-2xl font-bold text-red-900">
            {(effectiveness.metrics.error_rate * 100).toFixed(2)}%
          </p>
          <p className="text-xs text-red-700 mt-1">
            {effectiveness.metrics.error_rate < 0.01 ? 'Excellent' : effectiveness.metrics.error_rate < 0.05 ? 'Good' : 'Needs Attention'}
          </p>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-900">Avg Response Time</span>
            <Activity className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-blue-900">
            {effectiveness.metrics.avg_response_time.toFixed(0)}ms
          </p>
          <p className="text-xs text-blue-700 mt-1">
            {effectiveness.metrics.avg_response_time < 200 ? 'Excellent' : effectiveness.metrics.avg_response_time < 500 ? 'Good' : 'Slow'}
          </p>
        </div>

        <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-yellow-900">Throttled Requests</span>
            <TrendingUp className="w-5 h-5 text-yellow-600" />
          </div>
          <p className="text-2xl font-bold text-yellow-900">
            {effectiveness.metrics.throttled_requests.toLocaleString()}
          </p>
          <p className="text-xs text-yellow-700 mt-1">
            {((effectiveness.metrics.throttled_requests / effectiveness.metrics.total_requests) * 100).toFixed(1)}% of total
          </p>
        </div>
      </div>

      {/* Metrics Breakdown Chart */}
      <div className="mb-8">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Metrics Breakdown</h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={metricsData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
            <Bar dataKey="value" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Response Time Comparison */}
      <div className="mb-8">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Response Time Performance</h4>
        <ResponsiveContainer width="100%" height={150}>
          <BarChart data={responseTimeData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" label={{ value: 'Milliseconds', position: 'insideBottom', offset: -5 }} />
            <YAxis type="category" dataKey="name" />
            <Tooltip formatter={(value: number) => `${value.toFixed(0)}ms`} />
            <Legend />
            <Bar dataKey="value" fill="#3b82f6" name="Current" />
            <Bar dataKey="target" fill="#10b981" name="Target" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recommendations */}
      {effectiveness.recommendations && effectiveness.recommendations.length > 0 && (
        <div className="mb-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-3">Recommendations</h4>
          <div className="space-y-2">
            {effectiveness.recommendations.map((recommendation, index) => (
              <div key={index} className="flex gap-3 p-3 bg-blue-50 rounded-lg">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </div>
                <p className="text-sm text-gray-700 pt-0.5">{recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analysis Period */}
      <div className="border-t pt-4">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Analysis Period:</span>
          <span className="font-medium">
            {new Date(effectiveness.analysis_period.start).toLocaleString()} - {new Date(effectiveness.analysis_period.end).toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm text-gray-600 mt-2">
          <span>Total Requests Analyzed:</span>
          <span className="font-medium">{effectiveness.metrics.total_requests.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
};

export default RateLimitChart;

// Made with Bob