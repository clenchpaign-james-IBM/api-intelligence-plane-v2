import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { ContributingFactor } from '../../types';

interface FactorsChartProps {
  factors: ContributingFactor[];
}

/**
 * Factors Chart Component
 * 
 * Visualizes contributing factors using Recharts:
 * - Bar chart showing factor weights
 * - Color-coded by trend direction
 * - Tooltip with detailed information
 */
const FactorsChart = ({ factors }: FactorsChartProps) => {
  // Prepare data for chart
  const chartData = factors.map((factor) => ({
    name: factor.factor.replace(/_/g, ' ').slice(0, 20), // Truncate long names
    weight: factor.weight * 100, // Convert to percentage
    current: factor.current_value,
    threshold: factor.threshold,
    trend: factor.trend,
    fullName: factor.factor.replace(/_/g, ' '),
  }));

  // Sort by weight descending
  chartData.sort((a, b) => b.weight - a.weight);

  // Color based on trend
  const getTrendColor = (trend: string) => {
    switch (trend.toLowerCase()) {
      case 'increasing':
        return '#ef4444'; // red-500
      case 'decreasing':
        return '#10b981'; // green-500
      case 'stable':
        return '#6b7280'; // gray-500
      case 'volatile':
        return '#f59e0b'; // amber-500
      default:
        return '#3b82f6'; // blue-500
    }
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-semibold text-gray-900 mb-2">{data.fullName}</p>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between gap-4">
              <span className="text-gray-600">Weight:</span>
              <span className="font-medium text-gray-900">{data.weight.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-gray-600">Current:</span>
              <span className="font-medium text-gray-900">{data.current.toFixed(2)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-gray-600">Threshold:</span>
              <span className="font-medium text-gray-900">{data.threshold.toFixed(2)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-gray-600">Trend:</span>
              <span
                className="font-medium capitalize"
                style={{ color: getTrendColor(data.trend) }}
              >
                {data.trend}
              </span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  if (factors.length === 0) {
    return (
      <div className="text-sm text-gray-500 text-center py-4">
        No contributing factors available
      </div>
    );
  }

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 10, right: 10, left: 0, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={80}
            tick={{ fontSize: 11, fill: '#6b7280' }}
          />
          <YAxis
            label={{ value: 'Weight (%)', angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#6b7280' } }}
            tick={{ fontSize: 11, fill: '#6b7280' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="weight" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getTrendColor(entry.trend)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-2 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: '#ef4444' }} />
          <span className="text-gray-600">Increasing</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: '#10b981' }} />
          <span className="text-gray-600">Decreasing</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: '#6b7280' }} />
          <span className="text-gray-600">Stable</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: '#f59e0b' }} />
          <span className="text-gray-600">Volatile</span>
        </div>
      </div>
    </div>
  );
};

export default FactorsChart;

// Made with Bob