import { Sparkles, CheckCircle } from 'lucide-react';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import type { Recommendation, RecommendationPriority, RecommendationStatus, RecommendationType } from '../../types';

interface RecommendationCardProps {
  recommendation: Recommendation;
  onClick?: () => void;
  onApply?: (id: string) => void;
  detailed?: boolean;
}

/**
 * RecommendationCard Component
 * 
 * Displays a single optimization recommendation with:
 * - Title and description
 * - Priority, status, and type badges
 * - Expected impact metrics
 * - Implementation effort and cost savings
 * - Optional detailed view with implementation steps
 */
const RecommendationCard = ({ recommendation, onClick, onApply, detailed = false }: RecommendationCardProps) => {
  const [showAiInsights, setShowAiInsights] = useState(false);

  // Fetch AI insights when detailed view is shown
  const { data: aiInsights, isLoading: insightsLoading } = useQuery({
    queryKey: ['recommendation-insights', recommendation.id],
    queryFn: () => api.recommendations.getInsights(recommendation.id),
    enabled: detailed && showAiInsights,
  });

  // Priority badge color
  const getPriorityColor = (priority: RecommendationPriority) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Status badge color
  const getStatusColor = (status: RecommendationStatus) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'implemented': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-gray-100 text-gray-800';
      case 'expired': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Type display name
  const getTypeDisplayName = (type: RecommendationType) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  if (detailed) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {recommendation.title}
          </h2>
          <p className="text-gray-600">{recommendation.description}</p>
          <div className="flex items-center gap-2 mt-4">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(recommendation.priority)}`}>
              {recommendation.priority.toUpperCase()}
            </span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(recommendation.status)}`}>
              {recommendation.status.replace('_', ' ').toUpperCase()}
            </span>
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
              {getTypeDisplayName(recommendation.recommendation_type)}
            </span>
          </div>
        </div>

        {/* Impact Details */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Expected Impact</h3>
          <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Current Value</p>
                <p className="text-2xl font-bold text-gray-900">
                  {recommendation.estimated_impact.current_value.toFixed(2)}ms
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Expected Value</p>
                <p className="text-2xl font-bold text-green-600">
                  {recommendation.estimated_impact.expected_value.toFixed(2)}ms
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Improvement</p>
                <p className="text-2xl font-bold text-blue-600">
                  +{recommendation.estimated_impact.improvement_percentage.toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Confidence</p>
                <p className="text-2xl font-bold text-purple-600">
                  {(recommendation.estimated_impact.confidence * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Implementation Steps */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Implementation Steps</h3>
          <ol className="space-y-2">
            {recommendation.implementation_steps.map((step, index) => (
              <li key={index} className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </span>
                <span className="text-gray-700 pt-0.5">{step}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* Additional Info */}
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">Implementation Effort</p>
          <p className="text-lg font-semibold text-gray-900 capitalize">
            {recommendation.implementation_effort}
          </p>
        </div>

        {/* AI Insights Section */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <button
            onClick={() => setShowAiInsights(!showAiInsights)}
            className="flex items-center gap-2 text-purple-600 hover:text-purple-700 font-medium text-sm"
          >
            <Sparkles className="w-4 h-4" />
            {showAiInsights ? 'Hide' : 'Show'} AI Insights
          </button>
          
          {showAiInsights && (
            <div className="mt-3 bg-purple-50 rounded-lg p-4">
              {insightsLoading ? (
                <div className="flex items-center gap-2 text-purple-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                  <span className="text-sm">Loading AI insights...</span>
                </div>
              ) : aiInsights ? (
                <div className="space-y-3">
                  {aiInsights.analysis && (
                    <div>
                      <h5 className="text-sm font-semibold text-purple-900 mb-1">Performance Analysis</h5>
                      <p className="text-sm text-purple-800">{aiInsights.analysis}</p>
                    </div>
                  )}
                  {aiInsights.prioritization_reasoning && (
                    <div>
                      <h5 className="text-sm font-semibold text-purple-900 mb-1">Priority Reasoning</h5>
                      <p className="text-sm text-purple-800">{aiInsights.prioritization_reasoning}</p>
                    </div>
                  )}
                  {aiInsights.implementation_guidance && aiInsights.implementation_guidance.length > 0 && (
                    <div>
                      <h5 className="text-sm font-semibold text-purple-900 mb-1">Implementation Guidance</h5>
                      <ul className="space-y-1">
                        {aiInsights.implementation_guidance.map((guidance: string, index: number) => (
                          <li key={index} className="text-sm text-purple-800 flex items-start gap-2">
                            <span className="text-purple-600 mt-0.5">•</span>
                            <span>{guidance}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {aiInsights.risk_assessment && (
                    <div>
                      <h5 className="text-sm font-semibold text-purple-900 mb-1">Risk Assessment</h5>
                      <p className="text-sm text-purple-800">{aiInsights.risk_assessment}</p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-purple-700">No AI insights available for this recommendation.</p>
              )}
            </div>
          )}
        </div>

        {/* Apply to Gateway Button */}
        {onApply && recommendation.status === 'pending' && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={() => onApply(recommendation.id)}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
            >
              <CheckCircle className="w-5 h-5" />
              Apply to Gateway
            </button>
            <p className="text-xs text-gray-500 mt-2 text-center">
              This will create or update the policy in the API Gateway
            </p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer"
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {recommendation.title}
          </h3>
          <p className="text-sm text-gray-600 line-clamp-2">
            {recommendation.description}
          </p>
        </div>
      </div>

      {/* Badges */}
      <div className="flex items-center gap-2 mb-4">
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(recommendation.priority)}`}>
          {recommendation.priority.toUpperCase()}
        </span>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(recommendation.status)}`}>
          {recommendation.status.replace('_', ' ').toUpperCase()}
        </span>
        <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
          {getTypeDisplayName(recommendation.recommendation_type)}
        </span>
      </div>

      {/* Impact */}
      <div className="bg-gray-50 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Expected Impact</span>
          <span className="text-lg font-bold text-green-600">
            +{recommendation.estimated_impact.improvement_percentage.toFixed(1)}%
          </span>
        </div>
        <div className="text-xs text-gray-600">
          <div className="flex justify-between">
            <span>Current: {recommendation.estimated_impact.current_value.toFixed(2)}ms</span>
            <span>Expected: {recommendation.estimated_impact.expected_value.toFixed(2)}ms</span>
          </div>
          <div className="mt-1">
            Confidence: {(recommendation.estimated_impact.confidence * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Effort & Apply Button */}
      <div className="flex items-center justify-between text-sm gap-2">
        <div className="flex items-center gap-2">
          <span className="text-gray-600">Effort:</span>
          <span className="font-medium text-gray-900 capitalize">
            {recommendation.implementation_effort}
          </span>
        </div>
        {onApply && recommendation.status === 'pending' && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onApply(recommendation.id);
            }}
            className="px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 transition-colors flex items-center gap-1"
          >
            <CheckCircle className="w-3 h-3" />
            Apply
          </button>
        )}
      </div>
    </div>
  );
};

export default RecommendationCard;

// Made with Bob