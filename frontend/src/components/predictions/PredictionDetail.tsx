import { X, AlertTriangle, Clock, TrendingUp, CheckCircle, XCircle, Sparkles, Calendar, Target, Activity } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import FactorsChart from './FactorsChart';
import type { Prediction } from '../../types';

interface PredictionDetailProps {
  prediction: Prediction;
  onClose: () => void;
}

/**
 * Prediction Detail Modal Component
 * 
 * Displays comprehensive prediction information in a modal overlay:
 * - Full prediction details
 * - Contributing factors with visualization
 * - AI-enhanced explanations (if available)
 * - Recommended actions
 * - Timeline information
 * - Confidence and severity indicators
 */
const PredictionDetail = ({ prediction, onClose }: PredictionDetailProps) => {
  // Extract AI enhancement data
  const aiExplanation = prediction.metadata?.ai_explanation as string | undefined;
  const isAiEnhanced = prediction.metadata?.ai_enhanced === true;

  // Severity colors
  const severityColors = {
    critical: 'bg-red-100 text-red-800 border-red-300',
    high: 'bg-orange-100 text-orange-800 border-orange-300',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    low: 'bg-blue-100 text-blue-800 border-blue-300',
  };

  // Status icons and colors
  const statusConfig = {
    active: {
      icon: <AlertTriangle className="w-5 h-5" />,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      label: 'Active',
    },
    resolved: {
      icon: <CheckCircle className="w-5 h-5" />,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      label: 'Resolved',
    },
    false_positive: {
      icon: <XCircle className="w-5 h-5" />,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
      label: 'False Positive',
    },
    expired: {
      icon: <Clock className="w-5 h-5" />,
      color: 'text-gray-400',
      bgColor: 'bg-gray-50',
      label: 'Expired',
    },
  };

  const currentStatus = statusConfig[prediction.status];

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
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
    if (hours < 24) return `${hours} hours`;
    const days = Math.floor(hours / 24);
    const remainingHours = hours % 24;
    return `${days} day${days !== 1 ? 's' : ''} ${remainingHours} hour${remainingHours !== 1 ? 's' : ''}`;
  };

  // Format prediction type
  const formatPredictionType = (type: string) => {
    return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-4xl bg-white rounded-lg shadow-xl">
          {/* Header */}
          <div className="flex items-start justify-between p-6 border-b border-gray-200">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <div className={`p-2 rounded-lg ${currentStatus.bgColor}`}>
                  <div className={currentStatus.color}>
                    {currentStatus.icon}
                  </div>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {prediction.api_name || `API ${prediction.api_id.slice(0, 8)}`}
                  </h2>
                  <p className="text-sm text-gray-500 font-mono">
                    ID: {prediction.id}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-3">
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium border ${
                    severityColors[prediction.severity]
                  }`}
                >
                  {prediction.severity.toUpperCase()}
                </span>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800 border border-gray-300">
                  {formatPredictionType(prediction.prediction_type)}
                </span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium border ${currentStatus.bgColor} ${currentStatus.color}`}>
                  {currentStatus.label}
                </span>
                {isAiEnhanced && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800 border border-purple-300">
                    <Sparkles className="w-4 h-4" />
                    AI Enhanced
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="ml-4 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6 max-h-[calc(100vh-200px)] overflow-y-auto">
            {/* Key Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <div className="flex items-center gap-2 text-blue-600 mb-1">
                  <Target className="w-4 h-4" />
                  <span className="text-sm font-medium">Confidence</span>
                </div>
                <p className="text-2xl font-bold text-blue-900">
                  {(prediction.confidence_score * 100).toFixed(1)}%
                </p>
              </div>
              
              <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                <div className="flex items-center gap-2 text-purple-600 mb-1">
                  <Calendar className="w-4 h-4" />
                  <span className="text-sm font-medium">Time Until Event</span>
                </div>
                <p className="text-2xl font-bold text-purple-900">
                  {getTimeUntil()}
                </p>
              </div>
              
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <div className="flex items-center gap-2 text-green-600 mb-1">
                  <Activity className="w-4 h-4" />
                  <span className="text-sm font-medium">Model Version</span>
                </div>
                <p className="text-2xl font-bold text-green-900">
                  {prediction.model_version}
                </p>
              </div>
            </div>

            {/* Timeline */}
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Timeline</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Predicted At:</span>
                  <span className="font-medium text-gray-900">{formatDate(prediction.predicted_at)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Expected Event Time:</span>
                  <span className="font-medium text-gray-900">{formatDate(prediction.predicted_time)}</span>
                </div>
                {prediction.actual_time && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Actual Event Time:</span>
                    <span className="font-medium text-gray-900">{formatDate(prediction.actual_time)}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Description */}
            {prediction.description && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
                <p className="text-gray-700">{prediction.description}</p>
              </div>
            )}

            {/* AI-Enhanced Explanation */}
            {isAiEnhanced && aiExplanation && (
              <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  <h3 className="text-lg font-semibold text-purple-900">AI Analysis</h3>
                </div>
                <div className="prose prose-sm max-w-none text-gray-700">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {aiExplanation}
                  </ReactMarkdown>
                </div>
              </div>
            )}

            {/* Contributing Factors */}
            {prediction.contributing_factors && prediction.contributing_factors.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Contributing Factors</h3>
                <div className="space-y-3">
                  {prediction.contributing_factors.map((factor, index) => (
                    <div key={index} className="bg-white rounded-lg p-4 border border-gray-200">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 capitalize">
                            {factor.factor.replace(/_/g, ' ')}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">
                            Current: <span className="font-medium">{factor.current_value.toFixed(2)}</span>
                            {' | '}
                            Threshold: <span className="font-medium">{factor.threshold.toFixed(2)}</span>
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            factor.trend === 'increasing' ? 'bg-red-100 text-red-800' :
                            factor.trend === 'decreasing' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {factor.trend === 'increasing' && '↑'}
                            {factor.trend === 'decreasing' && '↓'}
                            {factor.trend !== 'increasing' && factor.trend !== 'decreasing' && '→'}
                            {' '}{factor.trend}
                          </span>
                          <span className="text-sm font-medium text-gray-700">
                            Weight: {(factor.weight * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      {/* Progress bar showing current vs threshold */}
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              factor.current_value > factor.threshold ? 'bg-red-500' : 'bg-green-500'
                            }`}
                            style={{
                              width: `${Math.min(100, (factor.current_value / factor.threshold) * 100)}%`
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Factors Chart */}
                <div className="mt-4">
                  <FactorsChart factors={prediction.contributing_factors} />
                </div>
              </div>
            )}

            {/* Recommended Actions */}
            {prediction.recommended_actions && prediction.recommended_actions.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Recommended Actions</h3>
                <ul className="space-y-2">
                  {prediction.recommended_actions.map((action, index) => (
                    <li key={index} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium mt-0.5">
                        {index + 1}
                      </div>
                      <p className="text-gray-700 flex-1">{action}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Accuracy Information (if available) */}
            {prediction.actual_outcome && (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Prediction Accuracy</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Actual Outcome:</span>
                    <span className={`font-medium capitalize ${
                      prediction.actual_outcome === 'occurred' ? 'text-red-600' :
                      prediction.actual_outcome === 'prevented' ? 'text-green-600' :
                      'text-gray-600'
                    }`}>
                      {prediction.actual_outcome.replace('_', ' ')}
                    </span>
                  </div>
                  {prediction.accuracy_score !== undefined && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Accuracy Score:</span>
                      <span className="font-medium text-gray-900">
                        {(prediction.accuracy_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionDetail;

// Made with Bob
