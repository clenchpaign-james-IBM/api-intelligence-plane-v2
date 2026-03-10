import { Clock, AlertTriangle } from 'lucide-react';
import type { Prediction } from '../../types';

interface PredictionTimelineProps {
  predictions: Prediction[];
}

/**
 * Prediction Timeline Component
 * 
 * Visualizes predictions on a timeline showing:
 * - When predictions were made
 * - When events are predicted to occur
 * - Severity indicators
 * - Time remaining
 */
const PredictionTimeline = ({ predictions }: PredictionTimelineProps) => {
  // Sort predictions by predicted_time
  const sortedPredictions = [...predictions].sort((a, b) => {
    return new Date(a.predicted_time).getTime() - new Date(b.predicted_time).getTime();
  });

  // Get time range
  const now = new Date();
  const earliest = sortedPredictions[0]
    ? new Date(sortedPredictions[0].predicted_time)
    : now;
  const latest = sortedPredictions[sortedPredictions.length - 1]
    ? new Date(sortedPredictions[sortedPredictions.length - 1].predicted_time)
    : new Date(now.getTime() + 48 * 60 * 60 * 1000); // 48 hours from now

  // Calculate position on timeline (0-100%)
  const getPosition = (dateString: string) => {
    const date = new Date(dateString);
    const total = latest.getTime() - earliest.getTime();
    const current = date.getTime() - earliest.getTime();
    return Math.max(0, Math.min(100, (current / total) * 100));
  };

  // Severity colors
  const severityColors = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-blue-500',
  };

  // Format time
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Calculate hours until event
  const getHoursUntil = (dateString: string) => {
    const date = new Date(dateString);
    const diff = date.getTime() - now.getTime();
    return Math.floor(diff / (1000 * 60 * 60));
  };

  if (sortedPredictions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
        <Clock className="w-12 h-12 mx-auto mb-2 text-gray-400" />
        <p>No active predictions to display</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Timeline Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">
            Prediction Timeline (Next 48 Hours)
          </span>
        </div>
        <div className="text-xs text-gray-500">
          {formatTime(earliest.toISOString())} → {formatTime(latest.toISOString())}
        </div>
      </div>

      {/* Timeline Visualization */}
      <div className="relative">
        {/* Timeline bar */}
        <div className="absolute top-8 left-0 right-0 h-1 bg-gray-200 rounded-full" />

        {/* Current time marker */}
        <div
          className="absolute top-6 transform -translate-x-1/2"
          style={{ left: `${getPosition(now.toISOString())}%` }}
        >
          <div className="flex flex-col items-center">
            <div className="w-0.5 h-4 bg-green-500" />
            <div className="w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
            <div className="w-0.5 h-4 bg-green-500" />
            <span className="text-xs font-medium text-green-600 mt-1">Now</span>
          </div>
        </div>

        {/* Prediction markers */}
        <div
          className="relative pt-16"
          style={{
            minHeight: `${Math.max(180, 16 + Math.ceil(sortedPredictions.length / 3) * 60 + 80)}px`,
            paddingBottom: '1rem'
          }}
        >
          {sortedPredictions.map((prediction, index) => {
            const position = getPosition(prediction.predicted_time);
            const hoursUntil = getHoursUntil(prediction.predicted_time);
            const isOverdue = hoursUntil < 0;

            return (
              <div
                key={prediction.id}
                className="absolute transform -translate-x-1/2"
                style={{
                  left: `${position}%`,
                  top: `${16 + (index % 3) * 60}px`,
                }}
              >
                <div className="flex flex-col items-center">
                  {/* Connector line */}
                  <div className="w-0.5 h-8 bg-gray-300" />

                  {/* Marker */}
                  <div
                    className={`w-4 h-4 rounded-full border-2 border-white ${
                      severityColors[prediction.severity]
                    }`}
                    title={`${prediction.api_name || 'API'} - ${prediction.severity}`}
                  />

                  {/* Label */}
                  <div className="mt-2 text-center min-w-[100px]">
                    <div className="text-xs font-medium text-gray-900 truncate">
                      {prediction.api_name || `API ${prediction.api_id.slice(0, 8)}`}
                    </div>
                    <div className="text-xs text-gray-600">
                      {isOverdue ? (
                        <span className="text-red-600 font-medium">Overdue</span>
                      ) : (
                        `${hoursUntil}h`
                      )}
                    </div>
                    <div className="flex items-center justify-center gap-1 mt-1">
                      <AlertTriangle className="w-3 h-3 text-gray-400" />
                      <span className="text-xs text-gray-500 capitalize">
                        {prediction.prediction_type}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-8 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-center gap-6 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-gray-600">Critical</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500" />
            <span className="text-gray-600">High</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <span className="text-gray-600">Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-gray-600">Low</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionTimeline;

// Made with Bob