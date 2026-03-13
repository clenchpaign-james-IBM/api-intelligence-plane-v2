import { AlertTriangle, Clock, TrendingUp, CheckCircle, XCircle, Sparkles } from '../../utils/carbonIcons';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Tile, ClickableTile, Tag, ProgressBar, Button, Loading as CarbonLoading } from '@carbon/react';
import FactorsChart from './FactorsChart';
import { api } from '../../services/api';
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
  const [showAiExplanation, setShowAiExplanation] = useState(false);

  // Fetch AI explanation when detailed view is shown
  const { data: aiExplanation, isLoading: explanationLoading } = useQuery({
    queryKey: ['prediction-explanation', prediction.id],
    queryFn: () => api.predictions.getExplanation(prediction.id),
    enabled: detailed && showAiExplanation,
  });

  // Severity tag types
  const getSeverityTagType = (severity: string): 'red' | 'warm-gray' | 'magenta' | 'blue' => {
    switch (severity) {
      case 'critical': return 'red';
      case 'high': return 'warm-gray';
      case 'medium': return 'magenta';
      case 'low': return 'blue';
      default: return 'blue';
    }
  };

  // Status icons
  const statusIcons = {
    active: <AlertTriangle size={20} style={{ color: 'var(--cds-support-warning)' }} />,
    resolved: <CheckCircle size={20} style={{ color: 'var(--cds-support-success)' }} />,
    false_positive: <XCircle size={20} style={{ color: 'var(--cds-icon-secondary)' }} />,
    expired: <Clock size={20} style={{ color: 'var(--cds-icon-disabled)' }} />,
  };

  // Trend tag types
  const getTrendTagType = (trend: string): 'red' | 'green' | 'blue' | 'warm-gray' => {
    switch (trend) {
      case 'increasing': return 'red';
      case 'decreasing': return 'green';
      case 'stable': return 'blue';
      case 'volatile': return 'warm-gray';
      default: return 'blue';
    }
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

  const TileComponent = onClick && !detailed ? ClickableTile : Tile;
  const tileProps = onClick && !detailed ? { onClick } : {};

  return (
    <TileComponent {...tileProps} style={{
      padding: detailed ? 'var(--cds-spacing-07)' : 'var(--cds-spacing-06)',
      border: '1px solid var(--cds-border-subtle)',
      borderRadius: '4px'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 'var(--cds-spacing-05)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
          {statusIcons[prediction.status]}
          <div>
            <h3 style={{ fontWeight: 600, fontSize: '1.125rem', color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-02)' }}>
              {prediction.api_name || `API ${prediction.api_id.slice(0, 8)}`}
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)', textTransform: 'capitalize' }}>
              {prediction.prediction_type.replace('_', ' ')}
            </p>
          </div>
        </div>
        <Tag type={getSeverityTagType(prediction.severity)} size="md">
          {prediction.severity.toUpperCase()}
        </Tag>
      </div>

      {/* Description */}
      {prediction.description && (
        <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-05)', lineHeight: '1.5' }}>{prediction.description}</p>
      )}

      {/* Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--cds-spacing-05)', marginBottom: 'var(--cds-spacing-05)' }}>
        <div style={{ backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px', padding: 'var(--cds-spacing-04)', border: '1px solid var(--cds-border-subtle)' }}>
          <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Confidence</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
            <div style={{ flex: 1 }}>
              <ProgressBar
                label="Confidence"
                value={prediction.confidence * 100}
                max={100}
                size="small"
                hideLabel
              />
            </div>
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
              {Math.round(prediction.confidence * 100)}%
            </span>
          </div>
        </div>
        <div style={{ backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px', padding: 'var(--cds-spacing-04)', border: '1px solid var(--cds-border-subtle)' }}>
          <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-02)' }}>Time Until</p>
          <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--cds-text-primary)', display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-02)' }}>
            <Clock size={16} />
            {getTimeUntil()}
          </p>
        </div>
      </div>

      {/* Predicted Time */}
      <div style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-05)' }}>
        <span style={{ fontWeight: 600 }}>Predicted:</span> {formatDate(prediction.predicted_time)}
      </div>

      {/* Contributing Factors */}
      {detailed && prediction.contributing_factors.length > 0 && (
        <div style={{ marginBottom: 'var(--cds-spacing-06)' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-04)', display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-02)' }}>
            <TrendingUp size={16} />
            Contributing Factors
          </h4>
          <FactorsChart factors={prediction.contributing_factors} />
          <div style={{ marginTop: 'var(--cds-spacing-04)', display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-04)' }}>
            {prediction.contributing_factors.map((factor, index) => (
              <div key={index} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.875rem', backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px', padding: 'var(--cds-spacing-04)', border: '1px solid var(--cds-border-subtle)' }}>
                <div style={{ flex: 1 }}>
                  <span style={{ fontWeight: 600, color: 'var(--cds-text-primary)' }}>
                    {factor.factor.replace(/_/g, ' ')}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
                  <span style={{ color: 'var(--cds-text-primary)' }}>
                    {factor.current_value.toFixed(2)}
                  </span>
                  <span style={{ color: 'var(--cds-text-secondary)' }}>
                    (threshold: {factor.threshold.toFixed(2)})
                  </span>
                  <Tag type={getTrendTagType(factor.trend)} size="md">
                    {factor.trend.charAt(0).toUpperCase() + factor.trend.slice(1)}
                  </Tag>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Actions */}
      {detailed && prediction.recommended_actions.length > 0 && (
        <div style={{ marginBottom: 'var(--cds-spacing-06)' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-04)' }}>Recommended Actions</h4>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-03)' }}>
            {prediction.recommended_actions.map((action, index) => (
              <li key={index} style={{ fontSize: '0.875rem', color: 'var(--cds-text-primary)', display: 'flex', alignItems: 'flex-start', gap: 'var(--cds-spacing-03)' }}>
                <span style={{ color: 'var(--cds-link-primary)', marginTop: '2px' }}>•</span>
                <span>{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* AI Explanation Section */}
      {detailed && (
        <div style={{ marginTop: 'var(--cds-spacing-06)', paddingTop: 'var(--cds-spacing-06)', borderTop: '1px solid var(--cds-border-subtle)' }}>
          <Button
            kind="ghost"
            size="sm"
            renderIcon={Sparkles}
            onClick={() => setShowAiExplanation(!showAiExplanation)}
            style={{ color: 'var(--cds-link-primary)' }}
          >
            {showAiExplanation ? 'Hide' : 'Show'} AI Explanation
          </Button>
          
          {showAiExplanation && (
            <div style={{ marginTop: 'var(--cds-spacing-05)', backgroundColor: 'var(--cds-layer-accent)', borderRadius: '4px', padding: 'var(--cds-spacing-06)', border: '1px solid var(--cds-border-subtle)' }}>
              {explanationLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)' }}>
                  <CarbonLoading small withOverlay={false} />
                  <span style={{ fontSize: '0.875rem', color: 'var(--cds-text-primary)' }}>Loading AI explanation...</span>
                </div>
              ) : aiExplanation ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-04)' }}>
                  <div>
                    <h5 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-02)' }}>Analysis</h5>
                    <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-primary)' }}>{aiExplanation.analysis}</p>
                  </div>
                  {aiExplanation.reasoning && (
                    <div>
                      <h5 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-02)' }}>Reasoning</h5>
                      <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-primary)' }}>{aiExplanation.reasoning}</p>
                    </div>
                  )}
                  {aiExplanation.confidence_factors && aiExplanation.confidence_factors.length > 0 && (
                    <div>
                      <h5 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--cds-text-primary)', marginBottom: 'var(--cds-spacing-02)' }}>Confidence Factors</h5>
                      <ul style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-02)' }}>
                        {aiExplanation.confidence_factors.map((factor: string, index: number) => (
                          <li key={index} style={{ fontSize: '0.875rem', color: 'var(--cds-text-primary)', display: 'flex', alignItems: 'flex-start', gap: 'var(--cds-spacing-03)' }}>
                            <span style={{ color: 'var(--cds-link-primary)', marginTop: '2px' }}>•</span>
                            <span>{factor}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-primary)' }}>No AI explanation available for this prediction.</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Compact view - show factor count */}
      {!detailed && (
        <div style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>
          {prediction.contributing_factors.length} contributing factors •{' '}
          {prediction.recommended_actions.length} actions
        </div>
      )}

      {/* Accuracy (if available) */}
      {prediction.accuracy_score !== undefined && prediction.accuracy_score !== null && (
        <div style={{ marginTop: 'var(--cds-spacing-05)', paddingTop: 'var(--cds-spacing-05)', borderTop: '1px solid var(--cds-border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem' }}>
            <span style={{ color: 'var(--cds-text-secondary)' }}>Accuracy Score:</span>
            <span style={{ fontWeight: 600, color: 'var(--cds-text-primary)' }}>
              {Math.round(prediction.accuracy_score * 100)}%
            </span>
          </div>
        </div>
      )}
    </TileComponent>
  );
};

export default PredictionCard;

// Made with Bob