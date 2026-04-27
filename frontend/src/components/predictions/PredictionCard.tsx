import { AlertTriangle, Clock, TrendingUp, CheckCircle, XCircle, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import FactorsChart from './FactorsChart';
import type { Prediction } from '../../types';

interface PredictionCardProps {
  prediction: Prediction;
  onClick?: () => void;
  detailed?: boolean;
}

/**
 * Prediction Card Component
 * 
 * Displays a prediction with:
 * - Severity indicator
 * - Confidence score
 * - Predicted time
 * - Contributing factors
 * - Recommended actions
 */
const PredictionCard = ({ prediction, onClick, detailed = false }: PredictionCardProps) => {
  // AI explanation is already in metadata, no need to fetch
  const aiExplanation = prediction.metadata?.ai_explanation as string | undefined;
  const isAiEnhanced = prediction.metadata?.ai_enhanced === true;

  // Severity colors
  const severityColors = {
    critical: 'bg-red-100 text-red-800 border-red-300',
    high: 'bg-orange-100 text-orange-800 border-orange-300',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    low: 'bg-blue-100 text-blue-800 border-blue-300',
  };

  // Status icons
  const statusIcons = {
    active: <AlertTriangle className="w-5 h-5 text-yellow-500" />,
    resolved: <CheckCircle className="w-5 h-5 text-green-500" />,
    false_positive: <XCircle className="w-5 h-5 text-gray-500" />,
    expired: <Clock className="w-5 h-5 text-gray-400" />,
  };

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Calculate time until predicted event
  const getTimeUntil = () => {
    const now = new Date();
    const predicted = new Date(prediction.predicted_time);
    const diff = predicted.getTime() - now.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    
    if (hours < 0) return 'Overdue';
    if (hours < 24) return `${hours}h`;
    return `${Math.floor(hours / 24)}d ${hours % 24}h`;
  };

  return (
    <div
      className={`bg-white rounded-lg shadow hover:shadow-lg transition-shadow ${
        onClick ? 'cursor-pointer' : ''
      } ${detailed ? 'p-6' : 'p-4'}`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          {statusIcons[prediction.status]}
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900">
                {prediction.api_name || `API ${prediction.api_id.slice(0, 8)}`}
              </h3>
              {isAiEnhanced && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 border border-purple-300">
                  <Sparkles className="w-3 h-3" />
                  AI Enhanced
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 font-mono">
              ID: {prediction.api_id}
            </p>
            <p className="text-sm text-gray-600 capitalize">
              {prediction.prediction_type.replace('_', ' ')}
            </p>
          </div>
        </div>
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium border ${
            severityColors[prediction.severity]
          }`}
        >
          {prediction.severity.toUpperCase()}
        </span>
      </div>

      {/* Description */}
      {prediction.description && (
        <p className="text-sm text-gray-700 mb-3">{prediction.description}</p>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="bg-gray-50 rounded p-2">
          <p className="text-xs text-gray-600">Confidence</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${(prediction.confidence_score || 0) * 100}%` }}
              />
            </div>
            <span className="text-sm font-medium text-gray-900">
              {Math.round((prediction.confidence_score || 0) * 100)}%
            </span>
          </div>
        </div>
        <div className="bg-gray-50 rounded p-2">
          <p className="text-xs text-gray-600">Time Until</p>
          <p className="text-sm font-medium text-gray-900 flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {getTimeUntil()}
          </p>
        </div>
      </div>

      {/* Predicted Time */}
      <div className="text-xs text-gray-600 mb-3">
        <span className="font-medium">Predicted:</span> {formatDate(prediction.predicted_time)}
      </div>

      {/* Contributing Factors */}
      {detailed && prediction.contributing_factors.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-1">
            <TrendingUp className="w-4 h-4" />
            Contributing Factors
          </h4>
          <FactorsChart factors={prediction.contributing_factors} />
          <div className="mt-2 space-y-2">
            {prediction.contributing_factors.map((factor, index) => {
              // Trend colors
              const trendColors = {
                increasing: 'bg-red-100 text-red-700 border-red-200',
                decreasing: 'bg-green-100 text-green-700 border-green-200',
                stable: 'bg-blue-100 text-blue-700 border-blue-200',
                volatile: 'bg-orange-100 text-orange-700 border-orange-200',
              };
              
              return (
                <div key={index} className="flex items-center justify-between text-xs bg-gray-50 rounded p-2">
                  <div className="flex-1">
                    <span className="font-medium text-gray-900">
                      {factor.factor.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-700">
                      {factor.current_value.toFixed(2)}
                    </span>
                    <span className="text-gray-500">
                      (threshold: {factor.threshold.toFixed(2)})
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded border text-xs font-medium ${
                        trendColors[factor.trend as keyof typeof trendColors] || 'bg-gray-100 text-gray-700 border-gray-200'
                      }`}
                    >
                      {factor.trend.charAt(0).toUpperCase() + factor.trend.slice(1)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommended Actions */}
      {detailed && prediction.recommended_actions.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Recommended Actions</h4>
          <ul className="space-y-1">
            {prediction.recommended_actions.map((action, index) => (
              <li key={index} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">•</span>
                <span>{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* AI Explanation Section - Always show if available */}
      {detailed && isAiEnhanced && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-purple-600" />
            <h5 className="text-sm font-semibold text-purple-900">AI-Powered Analysis</h5>
          </div>
          
          <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-4 border border-purple-200">
            {aiExplanation ? (
              <div className="prose prose-sm prose-purple max-w-none text-purple-900">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {aiExplanation}
                </ReactMarkdown>
              </div>
            ) : (
              <p className="text-sm text-purple-700">AI explanation not available.</p>
            )}
          </div>
        </div>
      )}

      {/* Compact view - show factor count */}
      {!detailed && (
        <div className="text-xs text-gray-600">
          {prediction.contributing_factors.length} contributing factors •{' '}
          {prediction.recommended_actions.length} actions
        </div>
      )}

      {/* Accuracy (if available) */}
      {prediction.accuracy_score !== undefined && prediction.accuracy_score !== null && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Accuracy Score:</span>
            <span className="font-medium text-gray-900">
              {Math.round(prediction.accuracy_score * 100)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictionCard;

// Made with Bob