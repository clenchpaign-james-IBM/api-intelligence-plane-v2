// Quick test script to verify compliance API
// Run in browser console: import('./test-compliance-api.ts')

import apiClient from './services/api';

export async function testComplianceAPI() {
  const gatewayId = 'b8087fed-b617-442c-8f93-61507f12a642';
  
  console.log('=== Testing Compliance API ===');
  
  try {
    // Direct API call
    const response = await apiClient.get(
      `/api/v1/gateways/${gatewayId}/compliance/violations`,
      { params: { limit: 1000 } }
    );
    
    console.log('Direct API Response:', {
      status: response.status,
      dataType: typeof response.data,
      isArray: Array.isArray(response.data),
      length: Array.isArray(response.data) ? response.data.length : 'N/A',
      firstItem: Array.isArray(response.data) && response.data.length > 0 ? response.data[0] : null,
      rawData: response.data
    });
    
    // Test wrapping logic
    const violations = Array.isArray(response.data) ? response.data : [];
    console.log('After wrapping:', {
      violationsLength: violations.length,
      firstViolation: violations[0]
    });
    
    return {
      success: true,
      violationsCount: violations.length,
      violations
    };
  } catch (error) {
    console.error('API Test Failed:', error);
    return {
      success: false,
      error
    };
  }
}

// Auto-run
testComplianceAPI();

// Made with Bob
