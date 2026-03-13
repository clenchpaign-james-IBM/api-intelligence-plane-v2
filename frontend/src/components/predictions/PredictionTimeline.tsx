import { Clock, AlertTriangle } from '../../utils/carbonIcons';
import { Tile } from '@carbon/react';
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

  // Severity colors (Carbon colors)
  const severityColors = {
    critical: '#da1e28',
    high: '#ff832b',
    medium: '#f1c21b',
    low: '#0f62fe',
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
      <Tile style={{ padding: 'var(--cds-spacing-06)', textAlign: 'center' }}>
        <Clock size={48} style={{ color: 'var(--cds-icon-secondary)', margin: '0 auto var(--cds-spacing-03)' }} />
        <p style={{ color: 'var(--cds-text-secondary)' }}>No active predictions to display</p>
      </Tile>
    );
  }

  return (
    <Tile style={{ padding: 'var(--cds-spacing-07)', border: '1px solid var(--cds-border-subtle)', borderRadius: '4px' }}>
      {/* Timeline Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--cds-spacing-07)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
          <Clock size={20} style={{ color: 'var(--cds-text-secondary)' }} />
          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
            Prediction Timeline (Next 48 Hours)
          </span>
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--cds-text-helper)' }}>
          {formatTime(earliest.toISOString())} → {formatTime(latest.toISOString())}
        </div>
      </div>

      {/* Timeline Visualization */}
      <div style={{ position: 'relative' }}>
        {/* Timeline bar */}
        <div style={{ position: 'absolute', top: '32px', left: 0, right: 0, height: '4px', backgroundColor: 'var(--cds-border-subtle)', borderRadius: '2px' }} />

        {/* Current time marker */}
        <div
          style={{ position: 'absolute', top: '24px', left: `${getPosition(now.toISOString())}%`, transform: 'translateX(-50%)' }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ width: '2px', height: '16px', backgroundColor: 'var(--cds-support-success)' }} />
            <div style={{ width: '12px', height: '12px', backgroundColor: 'var(--cds-support-success)', borderRadius: '50%', border: '2px solid var(--cds-layer)' }} />
            <div style={{ width: '2px', height: '16px', backgroundColor: 'var(--cds-support-success)' }} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cds-support-success)', marginTop: 'var(--cds-spacing-02)' }}>Now</span>
          </div>
        </div>

        {/* Prediction markers */}
        <div
          style={{
            position: 'relative',
            paddingTop: '64px',
            minHeight: `${Math.max(180, 16 + Math.ceil(sortedPredictions.length / 3) * 60 + 80)}px`,
            paddingBottom: 'var(--cds-spacing-05)'
          }}
        >
          {sortedPredictions.map((prediction, index) => {
            const position = getPosition(prediction.predicted_time);
            const hoursUntil = getHoursUntil(prediction.predicted_time);
            const isOverdue = hoursUntil < 0;

            return (
              <div
                key={prediction.id}
                style={{
                  position: 'absolute',
                  left: `${position}%`,
                  top: `${16 + (index % 3) * 60}px`,
                  transform: 'translateX(-50%)'
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  {/* Connector line */}
                  <div style={{ width: '2px', height: '32px', backgroundColor: 'var(--cds-border-subtle)' }} />

                  {/* Marker */}
                  <div
                    style={{
                      width: '16px',
                      height: '16px',
                      borderRadius: '50%',
                      border: '2px solid var(--cds-layer)',
                      backgroundColor: severityColors[prediction.severity]
                    }}
                    title={`${prediction.api_name || 'API'} - ${prediction.severity}`}
                  />

                  {/* Label */}
                  <div style={{ marginTop: 'var(--cds-spacing-03)', textAlign: 'center', minWidth: '100px' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cds-text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {prediction.api_name || `API ${prediction.api_id.slice(0, 8)}`}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>
                      {isOverdue ? (
                        <span style={{ color: 'var(--cds-support-error)', fontWeight: 600 }}>Overdue</span>
                      ) : (
                        `${hoursUntil}h`
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--cds-spacing-02)', marginTop: 'var(--cds-spacing-02)' }}>
                      <AlertTriangle size={12} style={{ color: 'var(--cds-icon-secondary)' }} />
                      <span style={{ fontSize: '0.75rem', color: 'var(--cds-text-helper)', textTransform: 'capitalize' }}>
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
      <div style={{ marginTop: 'var(--cds-spacing-08)', paddingTop: 'var(--cds-spacing-06)', borderTop: '1px solid var(--cds-border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--cds-spacing-07)', fontSize: '0.875rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#da1e28' }} />
            <span style={{ color: 'var(--cds-text-secondary)' }}>Critical</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ff832b' }} />
            <span style={{ color: 'var(--cds-text-secondary)' }}>High</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#f1c21b' }} />
            <span style={{ color: 'var(--cds-text-secondary)' }}>Medium</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#0f62fe' }} />
            <span style={{ color: 'var(--cds-text-secondary)' }}>Low</span>
          </div>
        </div>
      </div>
    </Tile>
  );
};

export default PredictionTimeline;

// Made with Bob