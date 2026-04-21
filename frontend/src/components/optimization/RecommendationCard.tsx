import React from 'react';
import { OptimizationRecommendation } from '../../types/optimization';

interface Props {
  recommendation: OptimizationRecommendation;
  onClick: () => void;
}

export const RecommendationCard: React.FC<Props> = ({ recommendation, onClick }) => {
  const hasAIInsights = recommendation.ai_context && (
    recommendation.ai_context.performance_analysis ||
    recommendation.ai_context.implementation_guidance ||
    recommendation.ai_context.prioritization
  );

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div
      className="recommendation-card p-4 border rounded-lg cursor-pointer hover:shadow-md transition-shadow bg-white"
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-semibold text-lg flex-1">{recommendation.title}</h3>
        
        <div className="flex gap-2 ml-2">
          {/* Priority Badge */}
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(recommendation.priority)}`}>
            {recommendation.priority}
          </span>
          
          {/* NEW: AI Badge */}
          {hasAIInsights && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              🤖 AI Enhanced
            </span>
          )}
        </div>
      </div>
      
      {/* Description */}
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{recommendation.description}</p>
      
      {/* Metrics */}
      <div className="flex gap-4 text-xs text-gray-500 mb-3">
        <div>
          <span className="font-medium">Impact:</span>{' '}
          {recommendation.estimated_impact.improvement_percentage.toFixed(1)}%
        </div>
        <div>
          <span className="font-medium">Effort:</span> {recommendation.implementation_effort}
        </div>
        <div>
          <span className="font-medium">Type:</span> {recommendation.recommendation_type}
        </div>
      </div>
      
      {/* Show preview of AI guidance if available */}
      {hasAIInsights && recommendation.ai_context?.implementation_guidance && (
        <div className="mt-3 p-2 bg-purple-50 rounded text-xs text-gray-700 border border-purple-100">
          <span className="font-medium">💡 AI Guidance: </span>
          {recommendation.ai_context.implementation_guidance.substring(0, 100)}
          {recommendation.ai_context.implementation_guidance.length > 100 && '...'}
        </div>
      )}
    </div>
  );
};

// Made with Bob
