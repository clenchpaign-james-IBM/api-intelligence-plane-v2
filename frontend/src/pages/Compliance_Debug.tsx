// Temporary debug file to test violation display
// This helps us understand why violations aren't showing

import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getComplianceViolations } from '../services/compliance';

export const ComplianceDebug: React.FC = () => {
  const gatewayId = 'b8087fed-b617-442c-8f93-61507f12a642';
  const apiId = '3bded59e-c42d-489b-b52d-33ec9617ec87';

  const { data: violationsResponse, isLoading, error } = useQuery({
    queryKey: ['debug-violations', gatewayId, apiId],
    queryFn: () => getComplianceViolations({
      gateway_id: gatewayId,
      api_id: apiId,
      limit: 1000,
    }),
  });

  useEffect(() => {
    if (violationsResponse) {
      console.log('=== COMPLIANCE DEBUG ===');
      console.log('Response:', violationsResponse);
      console.log('Violations array:', violationsResponse.violations);
      console.log('Total violations:', violationsResponse.violations?.length || 0);
      
      if (violationsResponse.violations && violationsResponse.violations.length > 0) {
        console.log('First violation:', violationsResponse.violations[0]);
        console.log('First violation api_id:', violationsResponse.violations[0].api_id);
        console.log('Expected api_id:', apiId);
        console.log('IDs match:', violationsResponse.violations[0].api_id === apiId);
      }
    }
  }, [violationsResponse, apiId]);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {String(error)}</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Compliance Debug</h1>
      <div className="bg-white p-4 rounded shadow">
        <h2 className="font-semibold mb-2">Query Parameters:</h2>
        <pre className="bg-gray-100 p-2 rounded text-sm">
          {JSON.stringify({ gatewayId, apiId }, null, 2)}
        </pre>
        
        <h2 className="font-semibold mt-4 mb-2">Response:</h2>
        <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto max-h-96">
          {JSON.stringify(violationsResponse, null, 2)}
        </pre>
      </div>
    </div>
  );
};

// Made with Bob
