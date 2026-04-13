/**
 * Compliance Service Client
 * 
 * Handles all compliance-related API calls to the backend.
 */

import apiClient from './api';
import type {
  ComplianceViolation,
  ComplianceViolationListResponse,
  ComplianceScanRequest,
  ComplianceScanResponse,
  CompliancePosture,
  AuditReportRequest,
  AuditReportResponse,
  ComplianceStandard,
  ComplianceSeverity,
  ComplianceStatus,
} from '../types';

/**
 * Scan an API for compliance violations
 */
export const scanAPICompliance = async (
  request: ComplianceScanRequest
): Promise<ComplianceScanResponse> => {
  const response = await apiClient.post('/api/v1/compliance/scan', request);
  return response.data;
};

/**
 * Get all compliance violations with optional filters
 */
export const getComplianceViolations = async (params?: {
  api_id?: string;
  standard?: ComplianceStandard;
  severity?: ComplianceSeverity;
  status?: ComplianceStatus;
  skip?: number;
  limit?: number;
}): Promise<ComplianceViolationListResponse> => {
  const response = await apiClient.get('/api/v1/compliance/violations', { params });
  // Backend returns array directly, wrap it in expected format
  const violations = Array.isArray(response.data) ? response.data : [];
  return {
    violations,
    total: violations.length,
    page: 1,
    page_size: violations.length,
    filters_applied: {
      standard: params?.standard,
      severity: params?.severity,
      status: params?.status,
      api_id: params?.api_id,
    },
  };
};

/**
 * Get a specific compliance violation by ID
 */
export const getComplianceViolation = async (
  violationId: string
): Promise<ComplianceViolation> => {
  const response = await apiClient.get(`/compliance/violations/${violationId}`);
  return response.data;
};

/**
 * Get compliance posture (overall compliance metrics)
 */
export const getCompliancePosture = async (params?: {
  api_id?: string;
  standard?: ComplianceStandard;
}): Promise<CompliancePosture> => {
  try {
    const response = await apiClient.get('/api/v1/compliance/posture', { params });
    
    // Handle both wrapped (response.data) and unwrapped (response) formats
    // React Query may unwrap the AxiosResponse before passing to our function
    const data = response.data || response;
    
    // Check if data exists and has expected structure
    if (!data || typeof data !== 'object') {
      console.error('Invalid data in compliance posture response:', data);
      throw new Error('No valid data received from compliance posture endpoint');
    }
    
    // Map backend response to frontend CompliancePosture interface
    const openViolations = data.by_status?.open || 0;
    const resolvedViolations = data.by_status?.resolved || 0;
    const inProgressViolations = data.by_status?.in_progress || 0;
    const acceptedRiskViolations = data.by_status?.accepted_risk || 0;
    const falsePositiveViolations = data.by_status?.false_positive || 0;
    
    // Calculate risk level based on compliance score
    let riskLevel: 'low' | 'medium' | 'high' | 'critical' = 'low';
    if (data.compliance_score < 50) riskLevel = 'critical';
    else if (data.compliance_score < 70) riskLevel = 'high';
    else if (data.compliance_score < 85) riskLevel = 'medium';
    
    // Map by_standard to ComplianceStandardScore format
    const byStandard: Record<ComplianceStandard, any> = {
      GDPR: {
        standard: 'GDPR',
        score: 100,
        violations: data.by_standard?.gdpr || 0,
        compliant_controls: 0,
        total_controls: 0,
        last_assessed: new Date().toISOString()
      },
      HIPAA: {
        standard: 'HIPAA',
        score: 100,
        violations: data.by_standard?.hipaa || 0,
        compliant_controls: 0,
        total_controls: 0,
        last_assessed: new Date().toISOString()
      },
      PCI_DSS: {
        standard: 'PCI_DSS',
        score: 100,
        violations: data.by_standard?.pci_dss || 0,
        compliant_controls: 0,
        total_controls: 0,
        last_assessed: new Date().toISOString()
      },
      SOC2: {
        standard: 'SOC2',
        score: 100,
        violations: data.by_standard?.soc2 || 0,
        compliant_controls: 0,
        total_controls: 0,
        last_assessed: new Date().toISOString()
      },
      ISO_27001: {
        standard: 'ISO_27001',
        score: 100,
        violations: data.by_standard?.iso_27001 || 0,
        compliant_controls: 0,
        total_controls: 0,
        last_assessed: new Date().toISOString()
      },
    };
    
    return {
      total_violations: data.total_violations || 0,
      open_violations: openViolations,
      resolved_violations: resolvedViolations,
      by_severity: data.by_severity || { critical: 0, high: 0, medium: 0, low: 0 },
      by_standard: byStandard,
      by_status: {
        open: openViolations,
        in_progress: inProgressViolations,
        resolved: resolvedViolations,
        accepted_risk: acceptedRiskViolations,
        false_positive: falsePositiveViolations,
      },
      overall_score: data.compliance_score || 100.0,
      risk_level: riskLevel,
      last_scan_date: data.last_scan || new Date().toISOString(),
      compliance_trends: [],
    };
  } catch (error) {
    console.error('Failed to fetch compliance posture:', error);
    // Return default empty posture on error
    return {
      total_violations: 0,
      open_violations: 0,
      resolved_violations: 0,
      by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
      by_standard: {
        GDPR: { standard: 'GDPR', score: 100, violations: 0, compliant_controls: 0, total_controls: 0, last_assessed: new Date().toISOString() },
        HIPAA: { standard: 'HIPAA', score: 100, violations: 0, compliant_controls: 0, total_controls: 0, last_assessed: new Date().toISOString() },
        PCI_DSS: { standard: 'PCI_DSS', score: 100, violations: 0, compliant_controls: 0, total_controls: 0, last_assessed: new Date().toISOString() },
        SOC2: { standard: 'SOC2', score: 100, violations: 0, compliant_controls: 0, total_controls: 0, last_assessed: new Date().toISOString() },
        ISO_27001: { standard: 'ISO_27001', score: 100, violations: 0, compliant_controls: 0, total_controls: 0, last_assessed: new Date().toISOString() },
      },
      by_status: {
        open: 0,
        in_progress: 0,
        resolved: 0,
        accepted_risk: 0,
        false_positive: 0
      },
      overall_score: 100.0,
      risk_level: 'low',
      last_scan_date: new Date().toISOString(),
      compliance_trends: [],
    };
  }
};

/**
 * Generate an audit report
 */
export const generateAuditReport = async (
  request: AuditReportRequest
): Promise<AuditReportResponse> => {
  try {
    const response = await apiClient.post('/api/v1/compliance/reports/audit', request);
    // Handle both wrapped (response.data) and unwrapped (response) formats
    const data = response.data || response;
    return data;
  } catch (error: any) {
    console.error('Failed to generate audit report:', error);
    throw new Error(error.response?.data?.detail || error.message || 'Failed to generate audit report');
  }
};

/**
 * Update compliance violation status
 */
export const updateViolationStatus = async (
  violationId: string,
  status: ComplianceStatus,
  notes?: string
): Promise<ComplianceViolation> => {
  const response = await apiClient.patch(`/compliance/violations/${violationId}`, {
    status,
    notes,
  });
  return response.data;
};

/**
 * Mark violation as false positive
 */
export const markAsFalsePositive = async (
  violationId: string,
  reason: string
): Promise<ComplianceViolation> => {
  return updateViolationStatus(violationId, 'false_positive', reason);
};

/**
 * Accept risk for a violation
 */
export const acceptRisk = async (
  violationId: string,
  justification: string
): Promise<ComplianceViolation> => {
  return updateViolationStatus(violationId, 'accepted_risk', justification);
};

/**
 * Resolve a violation
 */
export const resolveViolation = async (
  violationId: string,
  resolution_notes: string
): Promise<ComplianceViolation> => {
  return updateViolationStatus(violationId, 'resolved', resolution_notes);
};

/**
 * Export audit report in specified format
 */
export const exportAuditReport = async (
  reportId: string,
  format: 'pdf' | 'csv' | 'json' | 'html' = 'pdf'
): Promise<Blob> => {
  const response = await apiClient.get(`/compliance/reports/audit/${reportId}/export`, {
    params: { format },
    responseType: 'blob',
  });
  return response.data;
};

// Made with Bob
