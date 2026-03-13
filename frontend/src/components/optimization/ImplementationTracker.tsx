import { CheckCircle, Circle, Clock, XCircle } from '../../utils/carbonIcons';
import type { Recommendation, RecommendationStatus } from '../../types';

interface ImplementationTrackerProps {
  recommendations: Recommendation[];
  title?: string;
}

/**
 * ImplementationTracker Component
 * 
 * Tracks the implementation status of optimization recommendations:
 * - Visual progress indicator
 * - Status breakdown by category
 * - Timeline of implementations
 * - Success metrics
 */
const ImplementationTracker = ({ recommendations, title = 'Implementation Progress' }: ImplementationTrackerProps) => {
  // Calculate statistics
  const total = recommendations.length;
  const implemented = recommendations.filter(r => r.status === 'implemented').length;
  const inProgress = recommendations.filter(r => r.status === 'in_progress').length;
  const pending = recommendations.filter(r => r.status === 'pending').length;
  const rejected = recommendations.filter(r => r.status === 'rejected').length;
  
  const completionPercentage = total > 0 ? (implemented / total) * 100 : 0;
  const activePercentage = total > 0 ? ((implemented + inProgress) / total) * 100 : 0;

  // Calculate total savings from implemented recommendations
  const totalSavings = recommendations
    .filter(r => r.status === 'implemented' && r.cost_savings)
    .reduce((sum, r) => sum + (r.cost_savings || 0), 0);

  // Calculate average improvement from implemented recommendations
  const implementedRecs = recommendations.filter(r => r.status === 'implemented');
  const avgImprovement = implementedRecs.length > 0
    ? implementedRecs.reduce((sum, r) => sum + r.estimated_impact.improvement_percentage, 0) / implementedRecs.length
    : 0;

  // Get status icon and color
  const getStatusIcon = (status: RecommendationStatus) => {
    switch (status) {
      case 'implemented':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'in_progress':
        return <Clock className="w-5 h-5 text-blue-600" />;
      case 'rejected':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: RecommendationStatus) => {
    switch (status) {
      case 'implemented': return 'text-green-600';
      case 'in_progress': return 'text-blue-600';
      case 'rejected': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">{title}</h3>

      {/* Overall Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Completion</span>
          <span className="text-sm font-bold text-gray-900">{completionPercentage.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
          <div className="h-full flex">
            <div
              className="bg-green-500 h-full transition-all duration-500"
              style={{ width: `${completionPercentage}%` }}
            ></div>
            <div
              className="bg-blue-400 h-full transition-all duration-500"
              style={{ width: `${(inProgress / total) * 100}%` }}
            ></div>
          </div>
        </div>
        <div className="flex items-center justify-between mt-2 text-xs text-gray-600">
          <span>{implemented} completed</span>
          <span>{inProgress} in progress</span>
          <span>{pending} pending</span>
        </div>
      </div>

      {/* Status Breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium text-green-900">Implemented</span>
          </div>
          <p className="text-2xl font-bold text-green-700">{implemented}</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">In Progress</span>
          </div>
          <p className="text-2xl font-bold text-blue-700">{inProgress}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Circle className="w-5 h-5 text-gray-600" />
            <span className="text-sm font-medium text-gray-900">Pending</span>
          </div>
          <p className="text-2xl font-bold text-gray-700">{pending}</p>
        </div>
        <div className="bg-red-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <XCircle className="w-5 h-5 text-red-600" />
            <span className="text-sm font-medium text-red-900">Rejected</span>
          </div>
          <p className="text-2xl font-bold text-red-700">{rejected}</p>
        </div>
      </div>

      {/* Impact Metrics */}
      {implemented > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Realized Benefits</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
              <p className="text-xs text-green-700 mb-1">Avg Performance Gain</p>
              <p className="text-2xl font-bold text-green-700">
                +{avgImprovement.toFixed(1)}%
              </p>
            </div>
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
              <p className="text-xs text-blue-700 mb-1">Monthly Savings</p>
              <p className="text-2xl font-bold text-blue-700">
                ${totalSavings.toFixed(0)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div>
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Recent Activity</h4>
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {recommendations
            .filter(r => r.status !== 'pending')
            .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
            .slice(0, 5)
            .map((rec) => (
              <div key={rec.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex-shrink-0 mt-0.5">
                  {getStatusIcon(rec.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {rec.title}
                  </p>
                  <p className={`text-xs ${getStatusColor(rec.status)} capitalize`}>
                    {rec.status.replace('_', ' ')}
                  </p>
                  {rec.implemented_at && (
                    <p className="text-xs text-gray-500 mt-1">
                      Completed {new Date(rec.implemented_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
                {rec.status === 'implemented' && rec.estimated_impact && (
                  <div className="flex-shrink-0 text-right">
                    <p className="text-sm font-bold text-green-600">
                      +{rec.estimated_impact.improvement_percentage.toFixed(0)}%
                    </p>
                  </div>
                )}
              </div>
            ))}
          {recommendations.filter(r => r.status !== 'pending').length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Circle className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">No activity yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImplementationTracker;

// Made with Bob