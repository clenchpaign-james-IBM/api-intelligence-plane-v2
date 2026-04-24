/**
 * Compliance Violation Card Component
 *
 * Displays individual compliance violation details with status management.
 * Used within API Compliance Cards in the API-centric compliance view.
 */

import React, { useState } from 'react';
import type { ComplianceViolation } from '../../types';
import { updateViolationStatus, markAsFalsePositive, acceptRisk } from '../../services/compliance';

interface ComplianceViolationCardProps {
  violation: ComplianceViolation;
  onUpdate?: () => void;
}

const getSeverityColor = (severity: string): string => {
  switch (severity) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'high':
      return 'bg-orange-100 text-orange-800 border-orange-300';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'low':
      return 'bg-blue-100 text-blue-800 border-blue-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'open':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'in_progress':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'resolved':
      return 'bg-green-100 text-green-800 border-green-300';
    case 'accepted_risk':
      return 'bg-purple-100 text-purple-800 border-purple-300';
    case 'false_positive':
      return 'bg-gray-100 text-gray-800 border-gray-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
};

const getStandardColor = (standard: string): string => {
  switch (standard) {
    case 'GDPR':
      return 'bg-blue-100 text-blue-800 border-blue-300';
    case 'HIPAA':
      return 'bg-green-100 text-green-800 border-green-300';
    case 'SOC2':
      return 'bg-purple-100 text-purple-800 border-purple-300';
    case 'PCI_DSS':
      return 'bg-orange-100 text-orange-800 border-orange-300';
    case 'ISO_27001':
      return 'bg-indigo-100 text-indigo-800 border-indigo-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
};

export const ComplianceViolationCard: React.FC<ComplianceViolationCardProps> = ({
  violation,
  onUpdate,
}) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState<string | null>(null);
  const [showActions, setShowActions] = useState(false);

  const handleStatusUpdate = async (newStatus: 'in_progress' | 'resolved') => {
    setIsUpdating(true);
    setUpdateMessage(null);
    
    try {
      await updateViolationStatus(violation.id, newStatus);
      setUpdateMessage(`Status updated to ${newStatus.replace('_', ' ')}`);
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (error) {
      setUpdateMessage(`Update failed: ${error}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleMarkFalsePositive = async () => {
    const reason = prompt('Please provide a reason for marking this as a false positive:');
    if (!reason) return;

    setIsUpdating(true);
    setUpdateMessage(null);
    
    try {
      await markAsFalsePositive(violation.id, reason);
      setUpdateMessage('Marked as false positive');
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (error) {
      setUpdateMessage(`Update failed: ${error}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleAcceptRisk = async () => {
    const justification = prompt('Please provide justification for accepting this risk:');
    if (!justification) return;

    setIsUpdating(true);
    setUpdateMessage(null);
    
    try {
      await acceptRisk(violation.id, justification);
      setUpdateMessage('Risk accepted');
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (error) {
      setUpdateMessage(`Update failed: ${error}`);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-orange-500">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="text-md font-semibold text-gray-900 mb-2">
            {violation.title}
          </h4>
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`px-2 py-1 rounded-full text-xs font-medium border ${getStandardColor(
                violation.compliance_standard
              )}`}
            >
              {violation.compliance_standard.replace('_', '-')}
            </span>
            <span
              className={`px-2 py-1 rounded-full text-xs font-medium border ${getSeverityColor(
                violation.severity
              )}`}
            >
              {violation.severity.toUpperCase()}
            </span>
            <span
              className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                violation.status
              )}`}
            >
              {violation.status.replace('_', ' ').toUpperCase()}
            </span>
            <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
              {violation.violation_type.replace(/_/g, ' ').toUpperCase()}
            </span>
          </div>
        </div>
        
        {violation.risk_score !== undefined && (
          <div className="ml-4 text-right">
            <div className="text-xs text-gray-500">Risk Score</div>
            <div className="text-xl font-bold text-orange-600">
              {violation.risk_score}
            </div>
          </div>
        )}
      </div>

      {/* Description */}
      <div className="mb-3">
        <p className="text-sm text-gray-700">{violation.description}</p>
      </div>

      {/* Regulation Reference */}
      <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <h5 className="text-xs font-semibold text-blue-900 mb-1">📋 Regulation Reference:</h5>
        <p className="text-xs text-blue-800">{violation.regulation_reference}</p>
      </div>

      {/* Evidence */}
      {violation.evidence && violation.evidence.length > 0 && (() => {
        // Deduplicate evidence by creating a unique key from type + description + source
        const uniqueEvidence = Array.from(
          new Map(
            violation.evidence.map(e => [
              `${e.type}-${e.description}-${e.source}`,
              e
            ])
          ).values()
        );
        
        return (
          <div className="mb-3">
            <h5 className="text-xs font-semibold text-gray-700 mb-2">
              Evidence: ({uniqueEvidence.length} {uniqueEvidence.length === 1 ? 'item' : 'items'})
            </h5>
            <div className="space-y-2">
              {uniqueEvidence.map((evidence, index) => {
                const collectedDate = evidence.collected_at ? new Date(evidence.collected_at) : null;
                const isValidDate = collectedDate && !isNaN(collectedDate.getTime());
                
                return (
                  <div key={index} className="p-2 bg-white rounded border border-gray-200">
                    <div className="flex items-start gap-2">
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium">
                        {evidence.type}
                      </span>
                      <div className="flex-1">
                        <p className="text-xs text-gray-700">{evidence.description}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          Source: {evidence.source}
                          {isValidDate && ` • ${collectedDate.toLocaleString()}`}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}

      {/* Remediation Steps */}
      {violation.remediation_steps && violation.remediation_steps.length > 0 && (
        <div className="mb-3 p-3 bg-green-50 rounded-lg border border-green-200">
          <h5 className="text-xs font-semibold text-green-900 mb-2">🔧 Remediation Steps:</h5>
          <ol className="list-decimal list-inside space-y-1">
            {violation.remediation_steps.map((step, index) => (
              <li key={index} className="text-xs text-green-800">{step}</li>
            ))}
          </ol>
        </div>
      )}

      {/* Remediation Documentation */}
      {violation.remediation_documentation && (
        <div className="mb-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
          <h5 className="text-xs font-semibold text-purple-900 mb-2">📝 Remediation Documentation:</h5>
          <div className="space-y-1 text-xs text-purple-800">
            <p><strong>Steps Taken:</strong></p>
            <ul className="list-disc list-inside ml-2">
              {violation.remediation_documentation.steps_taken.map((step, index) => (
                <li key={index}>{step}</li>
              ))}
            </ul>
            <p className="mt-2"><strong>Verification:</strong> {violation.remediation_documentation.verification_method}</p>
            <p><strong>Result:</strong> {violation.remediation_documentation.verification_result}</p>
            <p className="text-xs text-purple-600 mt-1">
              Documented by {violation.remediation_documentation.documented_by} on{' '}
              {new Date(violation.remediation_documentation.documented_at).toLocaleString()}
            </p>
          </div>
        </div>
      )}

      {/* Business Impact */}
      {violation.business_impact && (
        <div className="mb-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
          <h5 className="text-xs font-semibold text-yellow-900 mb-1">⚠️ Business Impact:</h5>
          <p className="text-xs text-yellow-800">{violation.business_impact}</p>
        </div>
      )}

      {/* Audit Information */}
      {(violation.last_audit_date || violation.next_audit_date) && (
        <div className="mb-3 text-xs text-gray-600">
          {violation.last_audit_date && (
            <div>Last Audit: {new Date(violation.last_audit_date).toLocaleDateString()}</div>
          )}
          {violation.next_audit_date && (
            <div>Next Audit: {new Date(violation.next_audit_date).toLocaleDateString()}</div>
          )}
        </div>
      )}

      {/* Timestamps */}
      <div className="mb-3 text-xs text-gray-500">
        <div>Detected: {new Date(violation.detected_at).toLocaleString()}</div>
        <div>Detection Method: {violation.detection_method?.replace(/_/g, ' ') || 'Unknown'}</div>
        {violation.resolved_at && (
          <div>Resolved: {new Date(violation.resolved_at).toLocaleString()}</div>
        )}
        {violation.remediated_at && (
          <div>Remediated: {new Date(violation.remediated_at).toLocaleString()}</div>
        )}
      </div>

      {/* Actions */}
      {violation.status === 'open' && (
        <div className="space-y-2">
          <div className="flex gap-2">
            <button
              onClick={() => handleStatusUpdate('in_progress')}
              disabled={isUpdating}
              className="px-3 py-1.5 bg-yellow-600 text-white text-sm rounded-lg hover:bg-yellow-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isUpdating ? 'Updating...' : 'Mark In Progress'}
            </button>
            <button
              onClick={() => handleStatusUpdate('resolved')}
              disabled={isUpdating}
              className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isUpdating ? 'Updating...' : 'Mark Resolved'}
            </button>
            <button
              onClick={() => setShowActions(!showActions)}
              className="px-3 py-1.5 bg-gray-600 text-white text-sm rounded-lg hover:bg-gray-700 transition-colors"
            >
              More Actions
            </button>
          </div>
          
          {showActions && (
            <div className="flex gap-2 pt-2 border-t border-gray-200">
              <button
                onClick={handleMarkFalsePositive}
                disabled={isUpdating}
                className="px-3 py-1.5 bg-gray-500 text-white text-sm rounded-lg hover:bg-gray-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                Mark False Positive
              </button>
              <button
                onClick={handleAcceptRisk}
                disabled={isUpdating}
                className="px-3 py-1.5 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                Accept Risk
              </button>
            </div>
          )}
        </div>
      )}

      {violation.status === 'in_progress' && (
        <div className="flex gap-2">
          <button
            onClick={() => handleStatusUpdate('resolved')}
            disabled={isUpdating}
            className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isUpdating ? 'Updating...' : 'Mark Resolved'}
          </button>
        </div>
      )}

      {/* Update Message */}
      {updateMessage && (
        <div className="mt-3 p-2 bg-gray-100 rounded-lg border border-gray-300">
          <p className="text-xs text-gray-700">{updateMessage}</p>
        </div>
      )}
    </div>
  );
};

// Made with Bob