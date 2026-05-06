/**
 * Prediction Remediation Panel Component
 * 
 * Main panel for managing prediction auto-remediation.
 * Displays remediation plan, actions, and provides controls for:
 * - Generating remediation plans
 * - Executing remediation
 * - Verifying effectiveness
 * - Rolling back actions
 */

import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Play, 
  CheckCircle, 
  Undo2, 
  AlertTriangle,
  Clock,
  Shield,
  TrendingUp,
  RefreshCw
} from 'lucide-react';
import type { Prediction } from '../../types';
import { predictionService } from '../../services/prediction-service';
import type { 
  RemediationPlanResponse,
  RemediationRequest,
  RemediationExecutionResponse,
  VerificationResponse,
  RollbackResponse
} from '../../services/prediction-service';
import { RemediationActionCard } from './RemediationActionCard';
import { useNotification } from '../../contexts/NotificationContext';

interface PredictionRemediationPanelProps {
  prediction: Prediction;
  gatewayId: string;
  onUpdate?: () => void;
}

export const PredictionRemediationPanel: React.FC<PredictionRemediationPanelProps> = ({
  prediction,
  gatewayId,
  onUpdate,
}) => {
  const { showSuccess, showError } = useNotification();
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [isRemediating, setIsRemediating] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isRollingBack, setIsRollingBack] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [remediationStrategy, setRemediationStrategy] = useState<'conservative' | 'balanced' | 'aggressive'>('balanced');
  const [planResponse, setPlanResponse] = useState<RemediationPlanResponse | null>(null);
  const [executionResponse, setExecutionResponse] = useState<RemediationExecutionResponse | null>(null);
  const [verificationResponse, setVerificationResponse] = useState<VerificationResponse | null>(null);

  // Check if remediation is available for this prediction
  const hasRemediationPlan = prediction.remediation_plan || planResponse;
  const hasRemediationActions = prediction.remediation_actions && prediction.remediation_actions.length > 0;
  const remediationStatus = prediction.remediation_status || 'not_started';
  
  // Debug logging
  console.log('[PredictionRemediationPanel] Debug:', {
    predictionId: prediction.id,
    gatewayId,
    hasRemediationPlan,
    hasRemediationActions,
    remediationStatus,
    isGeneratingPlan,
    buttonDisabled: isGeneratingPlan || remediationStatus === 'in_progress'
  });

  // Real-time status updates - poll when remediation is in progress
  useEffect(() => {
    if (remediationStatus === 'in_progress' && onUpdate) {
      const interval = setInterval(() => {
        onUpdate();
      }, 3000); // Poll every 3 seconds
      
      return () => {
        clearInterval(interval);
      };
    }
  }, [remediationStatus, onUpdate]);

  // Handle generate plan
  const handleGeneratePlan = async (forceRegenerate: boolean = false) => {
    setIsGeneratingPlan(true);
    try {
      const response = await predictionService.generateRemediationPlan(
        gatewayId,
        prediction.id,
        forceRegenerate
      );
      setPlanResponse(response);
      showSuccess(
        'Plan Generated',
        `Remediation plan generated with ${response.plan.actions.length} actions. Estimated time: ${response.estimated_time_minutes} minutes.`
      );
      if (onUpdate) onUpdate();
    } catch (error) {
      showError('Plan Generation Failed', `Failed to generate remediation plan: ${error}`);
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  // Handle execute remediation
  const handleExecuteRemediation = async (autoApprove: boolean = false) => {
    if (!autoApprove && planResponse?.requires_approval) {
      setShowApprovalModal(true);
      return;
    }

    setIsRemediating(true);
    try {
      const request: RemediationRequest = {
        remediation_strategy: remediationStrategy,
        auto_approve: autoApprove,
      };
      const response = await predictionService.remediate(gatewayId, prediction.id, request);
      setExecutionResponse(response);
      const completedCount = response.actions?.filter(a => a.status === 'completed').length || 0;
      showSuccess(
        'Remediation Applied',
        `${completedCount} actions completed successfully.`
      );
      if (onUpdate) onUpdate();
    } catch (error) {
      showError('Remediation Failed', `Failed to execute remediation: ${error}`);
    } finally {
      setIsRemediating(false);
      setShowApprovalModal(false);
    }
  };

  // Handle verify remediation
  const handleVerifyRemediation = async () => {
    setIsVerifying(true);
    try {
      const response = await predictionService.verifyRemediation(gatewayId, prediction.id);
      setVerificationResponse(response);
      showSuccess(
        'Verification Complete',
        `Remediation effectiveness: ${Math.round(response.effectiveness_score * 100)}%`
      );
      if (onUpdate) onUpdate();
    } catch (error) {
      showError('Verification Failed', `Failed to verify remediation: ${error}`);
    } finally {
      setIsVerifying(false);
    }
  };

  // Handle rollback
  const handleRollback = async (actionId?: string) => {
    if (!confirm(actionId 
      ? 'Are you sure you want to rollback this action?' 
      : 'Are you sure you want to rollback all remediation actions?')) {
      return;
    }

    setIsRollingBack(true);
    try {
      const response = await predictionService.rollback(gatewayId, prediction.id, actionId);
      showSuccess(
        'Rollback Complete',
        `${response.rolled_back_actions.length} action(s) rolled back successfully.`
      );
      if (onUpdate) onUpdate();
    } catch (error) {
      showError('Rollback Failed', `Failed to rollback remediation: ${error}`);
    } finally {
      setIsRollingBack(false);
    }
  };

  // Get status color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'plan_generated':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'rolled_back':
        return 'bg-gray-100 text-gray-800 border-gray-300';
      case 'not_started':
      default:
        return 'bg-gray-100 text-gray-600 border-gray-300';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="w-6 h-6 text-blue-600" />
            Auto-Remediation
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            AI-powered remediation for predicted API failures
          </p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(
            remediationStatus
          )}`}
        >
          {remediationStatus.replace('_', ' ').toUpperCase()}
        </span>
      </div>

      {/* Remediation Plan Summary */}
      {hasRemediationPlan && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">Remediation Plan</h4>
              <p className="text-sm text-blue-800 mb-3">
                {(planResponse?.plan || prediction.remediation_plan)?.summary}
              </p>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-white/50 rounded p-2">
                  <p className="text-xs text-blue-700">Actions</p>
                  <p className="text-lg font-bold text-blue-900">
                    {(planResponse?.plan || prediction.remediation_plan)?.actions.length || 0}
                  </p>
                </div>
                <div className="bg-white/50 rounded p-2">
                  <p className="text-xs text-blue-700">Est. Time</p>
                  <p className="text-lg font-bold text-blue-900">
                    {(planResponse?.estimated_time_minutes || prediction.remediation_plan?.estimated_time_minutes || 0)} min
                  </p>
                </div>
                <div className="bg-white/50 rounded p-2">
                  <p className="text-xs text-blue-700">Risk Level</p>
                  <p className="text-lg font-bold text-blue-900 capitalize">
                    {(planResponse?.plan || prediction.remediation_plan)?.risk_level || 'Unknown'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Generate/Regenerate Plan */}
        <button
          onClick={() => handleGeneratePlan(!hasRemediationPlan)}
          disabled={isGeneratingPlan || remediationStatus === 'in_progress'}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
        >
          <Sparkles className={`w-4 h-4 ${isGeneratingPlan ? 'animate-spin' : ''}`} />
          {isGeneratingPlan ? 'Generating...' : hasRemediationPlan ? 'Regenerate Plan' : 'Generate Plan'}
        </button>

        {/* Execute Remediation */}
        {hasRemediationPlan && remediationStatus !== 'completed' && (
          <button
            onClick={() => handleExecuteRemediation(false)}
            disabled={isRemediating || remediationStatus === 'in_progress'}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed transition-colors"
          >
            <Play className={`w-4 h-4 ${isRemediating ? 'animate-pulse' : ''}`} />
            {isRemediating ? 'Applying...' : 'Execute Remediation'}
          </button>
        )}

        {/* Verify Remediation */}
        {remediationStatus === 'completed' && !prediction.remediation_verified && (
          <button
            onClick={handleVerifyRemediation}
            disabled={isVerifying}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-purple-400 disabled:cursor-not-allowed transition-colors"
          >
            <CheckCircle className={`w-4 h-4 ${isVerifying ? 'animate-pulse' : ''}`} />
            {isVerifying ? 'Verifying...' : 'Verify Effectiveness'}
          </button>
        )}

        {/* Rollback All */}
        {hasRemediationActions && remediationStatus === 'completed' && (
          <button
            onClick={() => handleRollback()}
            disabled={isRollingBack}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            <Undo2 className={`w-4 h-4 ${isRollingBack ? 'animate-spin' : ''}`} />
            {isRollingBack ? 'Rolling back...' : 'Rollback All'}
          </button>
        )}
      </div>

      {/* Strategy Selector */}
      {hasRemediationPlan && remediationStatus === 'plan_generated' && (
        <div className="bg-gray-50 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Remediation Strategy
          </label>
          <div className="flex gap-3">
            {(['conservative', 'balanced', 'aggressive'] as const).map((strategy) => (
              <button
                key={strategy}
                onClick={() => setRemediationStrategy(strategy)}
                className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                  remediationStrategy === strategy
                    ? 'border-blue-600 bg-blue-50 text-blue-900'
                    : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                }`}
              >
                <span className="font-medium capitalize">{strategy}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Remediation Actions */}
      {hasRemediationActions && (
        <div>
          <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Remediation Actions
          </h4>
          <div className="space-y-3">
            {prediction.remediation_actions!.map((action) => (
              <RemediationActionCard
                key={action.action_id}
                action={action}
                onRollback={handleRollback}
                isRollingBack={isRollingBack}
              />
            ))}
          </div>
        </div>
      )}

      {/* Verification Results */}
      {verificationResponse && (
        <div className={`rounded-lg p-4 border-2 ${
          verificationResponse.verified 
            ? 'bg-green-50 border-green-300' 
            : 'bg-yellow-50 border-yellow-300'
        }`}>
          <div className="flex items-start gap-3">
            {verificationResponse.verified ? (
              <CheckCircle className="w-6 h-6 text-green-600" />
            ) : (
              <AlertTriangle className="w-6 h-6 text-yellow-600" />
            )}
            <div className="flex-1">
              <h4 className={`text-sm font-semibold mb-2 ${
                verificationResponse.verified ? 'text-green-900' : 'text-yellow-900'
              }`}>
                Verification Results
              </h4>
              <p className={`text-sm mb-2 ${
                verificationResponse.verified ? 'text-green-800' : 'text-yellow-800'
              }`}>
                Effectiveness Score: {Math.round(verificationResponse.effectiveness_score * 100)}%
              </p>
              <p className={`text-xs ${
                verificationResponse.verified ? 'text-green-700' : 'text-yellow-700'
              }`}>
                Verified at: {new Date(verificationResponse.verification_time).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Approval Modal */}
      {showApprovalModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setShowApprovalModal(false)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-md w-full p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-bold text-gray-900 mb-4">Approve Remediation</h3>
            <p className="text-sm text-gray-700 mb-4">
              This remediation plan requires approval before execution. Review the actions above and confirm to proceed.
            </p>
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
              <p className="text-xs text-yellow-800">
                <strong>Warning:</strong> Remediation will modify gateway policies for the affected API. 
                Ensure you have reviewed the configuration changes.
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowApprovalModal(false)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleExecuteRemediation(true)}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Approve & Execute
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!hasRemediationPlan && remediationStatus === 'not_started' && (
        <div className="text-center py-8">
          <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">No remediation plan generated yet</p>
          <p className="text-sm text-gray-500">
            Click "Generate Plan" to create an AI-powered remediation plan for this prediction
          </p>
        </div>
      )}
    </div>
  );
};

export default PredictionRemediationPanel;

// Made with Bob