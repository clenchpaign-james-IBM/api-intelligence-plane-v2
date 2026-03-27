/**
 * Security API Service
 * 
 * Client for interacting with security scanning and vulnerability management endpoints.
 */

import axios from 'axios';
import type {
  Vulnerability,
  SecurityPosture,
  ScanResponse,
  RemediationResponse,
  VulnerabilityStatus,
  VulnerabilitySeverity,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Scan an API for security vulnerabilities
 */
export async function scanAPI(
  apiId: string,
  useAiEnhancement: boolean = true
): Promise<ScanResponse> {
  const response = await api.post<ScanResponse>('/api/v1/security/scan', {
    api_id: apiId,
    use_ai_enhancement: useAiEnhancement,
  });
  return response.data;
}

/**
 * Get vulnerabilities with optional filters
 */
export async function getVulnerabilities(params?: {
  api_id?: string;
  status?: VulnerabilityStatus;
  severity?: VulnerabilitySeverity;
  limit?: number;
}): Promise<Vulnerability[]> {
  const response = await api.get<Vulnerability[]>('/api/v1/security/vulnerabilities', {
    params,
  });
  return response.data;
}

/**
 * Get a specific vulnerability by ID
 */
export async function getVulnerability(vulnerabilityId: string): Promise<Vulnerability> {
  const response = await api.get<Vulnerability>(
    `/api/v1/security/vulnerabilities/${vulnerabilityId}`
  );
  return response.data;
}

/**
 * Remediate a vulnerability
 */
export async function remediateVulnerability(
  vulnerabilityId: string,
  remediationStrategy?: string
): Promise<RemediationResponse> {
  const response = await api.post<RemediationResponse>(
    `/api/v1/security/vulnerabilities/${vulnerabilityId}/remediate`,
    remediationStrategy ? { remediation_strategy: remediationStrategy } : undefined
  );
  return response.data;
}

/**
 * Verify remediation effectiveness
 */
export async function verifyRemediation(
  vulnerabilityId: string
): Promise<{ verified: boolean; details: any }> {
  const response = await api.post(
    `/api/v1/security/vulnerabilities/${vulnerabilityId}/verify`
  );
  return response.data;
}

/**
 * Get security posture metrics
 */
export async function getSecurityPosture(apiId?: string): Promise<SecurityPosture> {
  const response = await api.get<SecurityPosture>('/api/v1/security/posture', {
    params: apiId ? { api_id: apiId } : undefined,
  });
  return response.data;
}

/**
 * Get severity badge color
 */
export function getSeverityColor(severity: VulnerabilitySeverity): string {
  const colors: Record<VulnerabilitySeverity, string> = {
    critical: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-blue-100 text-blue-800 border-blue-200',
    info: 'bg-gray-100 text-gray-800 border-gray-200',
  };
  return colors[severity] || colors.info;
}

/**
 * Get status badge color
 */
export function getStatusColor(status: VulnerabilityStatus): string {
  const colors: Record<VulnerabilityStatus, string> = {
    open: 'bg-red-100 text-red-800 border-red-200',
    in_progress: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    remediated: 'bg-green-100 text-green-800 border-green-200',
    verified: 'bg-blue-100 text-blue-800 border-blue-200',
    false_positive: 'bg-gray-100 text-gray-800 border-gray-200',
    accepted_risk: 'bg-purple-100 text-purple-800 border-purple-200',
  };
  return colors[status] || colors.open;
}

/**
 * Get risk level color
 */
export function getRiskLevelColor(riskLevel: string): string {
  const colors: Record<string, string> = {
    critical: 'text-red-600',
    high: 'text-orange-600',
    medium: 'text-yellow-600',
    low: 'text-green-600',
  };
  return colors[riskLevel] || colors.medium;
}

/**
 * Format remediation time
 */
export function formatRemediationTime(milliseconds?: number): string {
  if (!milliseconds) return 'N/A';
  
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) return `${days}d ${hours % 24}h`;
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m`;
  return `${seconds}s`;
}

// Made with Bob
