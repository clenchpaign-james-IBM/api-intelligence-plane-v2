import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Heading, Button, Toggle, Select, SelectItem, Modal } from '@carbon/react';
import { AlertTriangle, TrendingUp, Filter, Sparkles } from '../utils/carbonIcons';
import Card from '../components/common/Card';
import PredictionCard from '../components/predictions/PredictionCard';
import PredictionTimeline from '../components/predictions/PredictionTimeline';
import Loading from '../components/common/Loading';
import Error from '../components/common/Error';
import { api } from '../services/api';
import type { Prediction, PredictionSeverity, PredictionStatus } from '../types';

/**
 * Predictions Page
 * 
 * Displays API failure predictions with:
 * - List of active predictions
 * - Filtering by severity and status
 * - Timeline visualization
 * - Detailed prediction cards
 */
const Predictions = () => {
  const [selectedSeverity, setSelectedSeverity] = useState<PredictionSeverity | 'all'>('all');
  const [selectedStatus, setSelectedStatus] = useState<PredictionStatus | 'all'>('all');
  const [selectedPrediction, setSelectedPrediction] = useState<Prediction | null>(null);
  const [useAi, setUseAi] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  // Fetch predictions
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['predictions', selectedSeverity, selectedStatus],
    queryFn: () => {
      const params: any = {};
      if (selectedSeverity !== 'all') params.severity = selectedSeverity;
      if (selectedStatus !== 'all') params.status = selectedStatus;
      return api.predictions.list(params);
    },
    refetchInterval: 60000, // Refetch every minute
  });

  // Generate new predictions
  const handleGeneratePredictions = async () => {
    setIsGenerating(true);
    try {
      // Use the standard generate endpoint with use_ai parameter
      // This endpoint can generate for all APIs when api_id is not provided
      await api.predictions.generate({ use_ai: useAi });
      refetch();
    } catch (err) {
      console.error('Failed to generate predictions:', err);
      alert('Failed to generate predictions. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div style={{ padding: 'var(--cds-spacing-06)' }}>
        <Loading message="Loading predictions..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{ padding: 'var(--cds-spacing-06)' }}>
        <Error
          message="Failed to load predictions"
          details={error as Error}
        />
      </div>
    );
  }

  const predictions = data?.predictions || [];
  const total = data?.total || 0;
  const activePredictions = predictions.filter((p: Prediction) => p.status === 'active');
  const criticalCount = predictions.filter((p: Prediction) => p.severity === 'critical').length;

  return (
    <div style={{ padding: 'var(--cds-spacing-06)' }}>
      {/* Header */}
      <div style={{ marginBottom: 'var(--cds-spacing-07)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--cds-spacing-06)' }}>
          <div>
            <Heading style={{ marginBottom: 'var(--cds-spacing-03)' }}>API Failure Predictions</Heading>
            <p style={{ color: 'var(--cds-text-secondary)', fontSize: '0.875rem' }}>
              {useAi ? 'LLM-enhanced predictions with detailed explanations' : 'Rule-based predictions of potential API failures'} 24-48 hours in advance
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
            {/* AI Toggle */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)', padding: 'var(--cds-spacing-04)', backgroundColor: 'var(--cds-layer-01)', borderRadius: '4px' }}>
              <Sparkles style={{ width: '20px', height: '20px', color: useAi ? 'var(--cds-support-info)' : 'var(--cds-icon-secondary)' }} />
              <Toggle
                id="ai-toggle"
                labelText="AI Enhanced"
                toggled={useAi}
                onToggle={() => setUseAi(!useAi)}
                size="sm"
              />
            </div>
            <Button
              kind="primary"
              renderIcon={TrendingUp}
              onClick={handleGeneratePredictions}
              disabled={isGenerating}
            >
              {isGenerating ? 'Generating...' : 'Generate Predictions'}
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--cds-spacing-06)' }}>
          <Card padding="md">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Active Predictions</p>
                <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>{activePredictions.length}</p>
              </div>
              <AlertTriangle style={{ width: '32px', height: '32px', color: 'var(--cds-support-warning)' }} />
            </div>
          </Card>
          <Card padding="md">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Critical Severity</p>
                <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-support-error)' }}>{criticalCount}</p>
              </div>
              <AlertTriangle style={{ width: '32px', height: '32px', color: 'var(--cds-support-error)' }} />
            </div>
          </Card>
          <Card padding="md">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>Total Predictions</p>
                <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>{predictions.length}</p>
              </div>
              <TrendingUp style={{ width: '32px', height: '32px', color: 'var(--cds-support-info)' }} />
            </div>
          </Card>
        </div>
      </div>

      {/* Filters */}
      <div style={{ marginBottom: 'var(--cds-spacing-08)' }}>
        <Card padding="md">
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-06)' }}>
          <Filter style={{ width: '20px', height: '20px', color: 'var(--cds-icon-secondary)' }} />
          <Select
            id="severity-select"
            labelText="Severity"
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value as PredictionSeverity | 'all')}
            size="sm"
            inline
          >
            <SelectItem value="all" text="All" />
            <SelectItem value="critical" text="Critical" />
            <SelectItem value="high" text="High" />
            <SelectItem value="medium" text="Medium" />
            <SelectItem value="low" text="Low" />
          </Select>
          <Select
            id="status-select"
            labelText="Status"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value as PredictionStatus | 'all')}
            size="sm"
            inline
          >
            <SelectItem value="all" text="All" />
            <SelectItem value="active" text="Active" />
            <SelectItem value="resolved" text="Resolved" />
            <SelectItem value="false_positive" text="False Positive" />
            <SelectItem value="expired" text="Expired" />
          </Select>
        </div>
        </Card>
      </div>

      {/* Timeline View */}
      {activePredictions.length > 0 && (
        <div style={{ marginBottom: 'var(--cds-spacing-08)' }}>
          <Heading style={{ fontSize: '1.25rem', marginBottom: 'var(--cds-spacing-06)' }}>Prediction Timeline</Heading>
          <PredictionTimeline predictions={activePredictions} />
        </div>
      )}

      {/* Predictions List */}
      <div>
        <Heading style={{ fontSize: '1.25rem', marginBottom: 'var(--cds-spacing-06)' }}>All Predictions</Heading>
        {predictions.length === 0 ? (
          <Card padding="lg">
            <div style={{ textAlign: 'center' }}>
              <AlertTriangle size={48} style={{ color: 'var(--cds-icon-secondary)', margin: '0 auto var(--cds-spacing-05)' }} />
              <p style={{ color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-03)' }}>No predictions found</p>
              <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-helper)' }}>
                Click "Generate Predictions" to analyze your APIs
              </p>
            </div>
          </Card>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-07)' }}>
            {predictions.map((prediction: Prediction, index: number) => (
              <div key={prediction.id} style={{ marginBottom: index < predictions.length - 1 ? 'var(--cds-spacing-07)' : '0' }}>
                <PredictionCard
                  prediction={prediction}
                  onClick={() => setSelectedPrediction(prediction)}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detailed View Modal */}
      {selectedPrediction && (
        <Modal
          open={true}
          onRequestClose={() => setSelectedPrediction(null)}
          modalHeading="Prediction Details"
          passiveModal
          size="lg"
        >
          <PredictionCard
            prediction={selectedPrediction}
            detailed
            onClick={() => {}}
          />
        </Modal>
      )}
    </div>
  );
};

export default Predictions;

// Made with Bob