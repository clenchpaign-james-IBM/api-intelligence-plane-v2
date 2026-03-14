import { Clock, AlertTriangle, Filter } from 'lucide-react';
import { useState } from 'react';
import type { Prediction, PredictionSeverity, PredictionStatus } from '../../types';

interface PredictionTimelineProps {
  predictions: Prediction[];
  onPredictionClick?: (prediction: Prediction) => void;
}

/**
 * Prediction Timeline Component
 * 
 * Visualizes predictions on a timeline showing:
 * - When predictions were made
 * - When events are predicted to occur
 * - Severity indicators
 * - Time remaining
 * 
 * Improved with collision detection to prevent overlapping entries
 */
const PredictionTimeline = ({ predictions, onPredictionClick }: PredictionTimelineProps) => {
  // Local filter state
  const [selectedSeverity, setSelectedSeverity] = useState<PredictionSeverity | 'all'>('all');
  const [selectedStatus, setSelectedStatus] = useState<PredictionStatus | 'all'>('all');

  // Filter predictions
  const filteredPredictions = predictions.filter((p) => {
    if (selectedSeverity !== 'all' && p.severity !== selectedSeverity) return false;
    if (selectedStatus !== 'all' && p.status !== selectedStatus) return false;
    return true;
  });

  // Sort predictions by predicted_time
  const sortedPredictions = [...filteredPredictions].sort((a, b) => {
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

  // Improved collision detection and vertical positioning
  const calculateVerticalPositions = () => {
    const positions: { [key: string]: number } = {};
    const occupiedRanges: Array<{ start: number; end: number; row: number }> = [];
    const minSeparation = 8; // Minimum horizontal separation in percentage
    const labelWidth = 12; // Approximate width of label in percentage

    sortedPredictions.forEach((prediction) => {
      const position = getPosition(prediction.predicted_time);
      const labelStart = position - labelWidth / 2;
      const labelEnd = position + labelWidth / 2;

      // Find the first available row where this label won't overlap
      let row = 0;
      let foundRow = false;

      while (!foundRow && row < 10) { // Max 10 rows
        const hasCollision = occupiedRanges.some(
          (range) =>
            range.row === row &&
            !(labelEnd < range.start - minSeparation || labelStart > range.end + minSeparation)
        );

        if (!hasCollision) {
          foundRow = true;
          occupiedRanges.push({ start: labelStart, end: labelEnd, row });
          positions[prediction.id] = row;
        } else {
          row++;
        }
      }

      // If no row found after 10 attempts, use the row anyway (fallback)
      if (!foundRow) {
        positions[prediction.id] = row;
      }
    });

    return positions;
  };

  const verticalPositions = calculateVerticalPositions();
  const maxRow = Math.max(...Object.values(verticalPositions), 0);

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
      {/* Timeline Header with Filters */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">
              Prediction Timeline (Next 48 Hours)
            </span>
          </div>

          {/* Filters - Inline */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <label className="text-xs font-medium text-gray-700">Severity:</label>
              <select
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value as PredictionSeverity | 'all')}
                className="px-2 py-1 border border-gray-300 rounded text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-gray-700">Status:</label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value as PredictionStatus | 'all')}
                className="px-2 py-1 border border-gray-300 rounded text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="active">Active</option>
                <option value="resolved">Resolved</option>
                <option value="false_positive">False Positive</option>
                <option value="expired">Expired</option>
              </select>
            </div>
            <div className="text-xs text-gray-600">
              {sortedPredictions.length} of {predictions.length}
            </div>
          </div>
        </div>

        {/* Time range */}
        <div className="text-xs text-gray-500 mt-2">
          {formatTime(earliest.toISOString())} → {formatTime(latest.toISOString())}
        </div>
      </div>

      {/* Timeline Visualization */}
      <div className="relative overflow-x-auto px-20">
        {/* Timeline bar */}
        <div className="absolute top-8 left-20 right-20 h-1 bg-gray-200 rounded-full" />

        {/* Current time marker - Enhanced visibility */}
        <div
          className="absolute top-6 z-20"
          style={{
            left: `calc(${getPosition(now.toISOString())}% + 5rem)`,
            transform: 'translateX(-50%)'
          }}
        >
          <div className="flex flex-col items-center">
            <div className="w-1 h-6 bg-green-600 rounded-t" />
            <div className="w-5 h-5 bg-green-600 rounded-full border-3 border-white shadow-lg ring-2 ring-green-300 animate-pulse" />
            <div className="w-1 h-6 bg-green-600 rounded-b" />
            <div className="mt-2 px-2 py-1 bg-green-600 text-white text-xs font-bold rounded shadow-md whitespace-nowrap">
              NOW
            </div>
          </div>
        </div>

        {/* Prediction markers with collision-free positioning */}
        <div
          className="relative pt-16"
          style={{
            minHeight: `${Math.max(200, 16 + (maxRow + 1) * 80 + 80)}px`,
            paddingBottom: '2rem'
          }}
        >
          {sortedPredictions.map((prediction) => {
            const position = getPosition(prediction.predicted_time);
            const row = verticalPositions[prediction.id] || 0;
            const hoursUntil = getHoursUntil(prediction.predicted_time);
            const isOverdue = hoursUntil < 0;

            return (
              <div
                key={prediction.id}
                className="absolute transition-all duration-200 hover:z-20"
                style={{
                  left: `calc(${position}% + 5rem)`,
                  transform: 'translateX(-50%)',
                  top: `${16 + row * 80}px`,
                }}
              >
                <div className="flex flex-col items-center">
                  {/* Connector line */}
                  <div className="w-0.5 h-8 bg-gray-300" />

                  {/* Marker - Clickable */}
                  <div
                    className={`w-4 h-4 rounded-full border-2 border-white shadow-md ${
                      severityColors[prediction.severity]
                    } hover:scale-150 transition-transform cursor-pointer`}
                    title={`Click to view details: ${prediction.api_name || 'API'} - ${prediction.severity}`}
                    onClick={() => onPredictionClick?.(prediction)}
                  />

                  {/* Label - Simplified without Overdue */}
                  <div className="mt-2 text-center min-w-[120px] max-w-[140px] bg-white rounded-lg shadow-sm border border-gray-200 p-2 hover:shadow-md transition-shadow cursor-pointer"
                       onClick={() => onPredictionClick?.(prediction)}>
                    <div className="text-xs font-semibold text-gray-900 truncate mb-1" title={prediction.api_name || `API ${prediction.api_id}`}>
                      {prediction.api_name || `API ${prediction.api_id.slice(0, 8)}`}
                    </div>
                    
                    <div className="text-xs text-gray-600 mb-1">
                      {isOverdue ? (
                        <span className="text-red-600 font-medium">Overdue</span>
                      ) : (
                        `${hoursUntil}h`
                      )}
                    </div>

                    <div className="flex items-center justify-center gap-1">
                      <AlertTriangle className="w-3 h-3 text-gray-400" />
                      <span className="text-xs text-gray-500 capitalize truncate">
                        {prediction.prediction_type.replace('_', ' ')}
                      </span>
                    </div>

                    {/* Confidence indicator */}
                    <div className="mt-1 w-full bg-gray-200 rounded-full h-1">
                      <div
                        className="bg-blue-500 h-1 rounded-full"
                        style={{ width: `${(prediction.confidence_score || 0) * 100}%` }}
                      />
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