import type { EstimatedImpact } from '../../types';

interface ImpactChartProps {
  impact: EstimatedImpact;
  title?: string;
}

/**
 * ImpactChart Component
 * 
 * Visualizes the estimated impact of an optimization recommendation:
 * - Current vs expected value comparison
 * - Improvement percentage
 * - Confidence level
 * - Visual bar chart representation
 */
const ImpactChart = ({ impact, title = 'Expected Impact' }: ImpactChartProps) => {
  const improvementPercentage = impact.improvement_percentage;
  const confidencePercentage = impact.confidence * 100;
  
  // Calculate bar widths (relative to max value)
  const maxValue = Math.max(impact.current_value, impact.expected_value);
  const currentWidth = (impact.current_value / maxValue) * 100;
  const expectedWidth = (impact.expected_value / maxValue) * 100;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      {/* Metric Info */}
      <div className="mb-6">
        <p className="text-sm text-gray-600 mb-2">Metric: {impact.metric}</p>
        <div className="flex items-center justify-between">
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">Current</p>
            <p className="text-xl font-bold text-gray-900">
              {impact.current_value.toFixed(2)}ms
            </p>
          </div>
          <div className="flex-1 mx-4 flex items-center">
            <div className="flex-1 h-px bg-gray-300"></div>
            <div className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
              -{improvementPercentage.toFixed(1)}%
            </div>
            <div className="flex-1 h-px bg-gray-300"></div>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">Expected</p>
            <p className="text-xl font-bold text-green-600">
              {impact.expected_value.toFixed(2)}ms
            </p>
          </div>
        </div>
      </div>

      {/* Bar Chart */}
      <div className="space-y-4 mb-6">
        {/* Current Value Bar */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-gray-700">Current Performance</span>
            <span className="text-sm text-gray-600">{impact.current_value.toFixed(2)}ms</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
            <div
              className="bg-gray-600 h-full rounded-full flex items-center justify-end pr-2"
              style={{ width: `${currentWidth}%` }}
            >
              <span className="text-xs text-white font-medium">100%</span>
            </div>
          </div>
        </div>

        {/* Expected Value Bar */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-gray-700">Expected Performance</span>
            <span className="text-sm text-green-600">{impact.expected_value.toFixed(2)}ms</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
            <div
              className="bg-gradient-to-r from-green-500 to-green-600 h-full rounded-full flex items-center justify-end pr-2"
              style={{ width: `${expectedWidth}%` }}
            >
              <span className="text-xs text-white font-medium">
                {(100 - improvementPercentage).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Improvement Metrics */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
          <p className="text-xs text-green-700 mb-1">Improvement</p>
          <p className="text-2xl font-bold text-green-700">
            +{improvementPercentage.toFixed(1)}%
          </p>
          <p className="text-xs text-green-600 mt-1">
            {(impact.current_value - impact.expected_value).toFixed(2)}ms faster
          </p>
        </div>
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
          <p className="text-xs text-blue-700 mb-1">Confidence</p>
          <p className="text-2xl font-bold text-blue-700">
            {confidencePercentage.toFixed(0)}%
          </p>
          <p className="text-xs text-blue-600 mt-1">
            {confidencePercentage >= 80 ? 'High' : confidencePercentage >= 60 ? 'Medium' : 'Low'} certainty
          </p>
        </div>
      </div>

      {/* Confidence Indicator */}
      <div className="mt-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-600">Prediction Confidence</span>
          <span className="text-xs font-medium text-gray-900">{confidencePercentage.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full rounded-full ${
              confidencePercentage >= 80
                ? 'bg-green-500'
                : confidencePercentage >= 60
                ? 'bg-yellow-500'
                : 'bg-orange-500'
            }`}
            style={{ width: `${confidencePercentage}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};

export default ImpactChart;

// Made with Bob