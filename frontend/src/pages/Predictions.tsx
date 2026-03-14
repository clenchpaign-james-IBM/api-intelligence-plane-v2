import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, TrendingUp, Filter, Sparkles } from 'lucide-react';
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
      <div className="p-6">
        <Loading message="Loading predictions..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-6">
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
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">API Failure Predictions</h1>
            <p className="mt-2 text-sm text-gray-600">
              {useAi ? 'LLM-enhanced predictions with detailed explanations' : 'Rule-based predictions of potential API failures'} 24-48 hours in advance
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* AI Toggle Switch */}
            <div className="flex items-center gap-2 bg-white rounded-lg shadow px-4 py-2">
              <Sparkles className={`w-5 h-5 ${useAi ? 'text-purple-600' : 'text-gray-400'}`} />
              <span className="text-sm font-medium text-gray-700">AI Enhanced</span>
              <button
                onClick={() => setUseAi(!useAi)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  useAi ? 'bg-purple-600' : 'bg-gray-300'
                }`}
                role="switch"
                aria-checked={useAi}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    useAi ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            <button
              onClick={handleGeneratePredictions}
              disabled={isGenerating}
              className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
                isGenerating
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              } text-white`}
            >
              <TrendingUp className="w-5 h-5" />
              {isGenerating ? 'Generating...' : 'Generate Predictions'}
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Predictions</p>
                <p className="text-2xl font-bold text-gray-900">{activePredictions.length}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Critical Severity</p>
                <p className="text-2xl font-bold text-red-600">{criticalCount}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Predictions</p>
                <p className="text-2xl font-bold text-gray-900">{predictions.length}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Timeline View */}
      {activePredictions.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Prediction Timeline</h2>
          <PredictionTimeline
            predictions={activePredictions}
            onPredictionClick={setSelectedPrediction}
          />
        </div>
      )}

      {/* Predictions List */}
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">All Predictions</h2>
        {predictions.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No predictions found</p>
            <p className="text-sm text-gray-500 mt-2">
              Click "Generate Predictions" to analyze your APIs
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {predictions.map((prediction: Prediction) => (
              <PredictionCard
                key={prediction.id}
                prediction={prediction}
                onClick={() => setSelectedPrediction(prediction)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Detailed View Modal */}
      {selectedPrediction && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedPrediction(null)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <PredictionCard
                prediction={selectedPrediction}
                detailed
                onClick={() => {}}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Predictions;

// Made with Bob