/**
 * Query History Component
 * 
 * Displays conversation history with queries and responses.
 */

import React from 'react';
import { Query } from '../../types';
import { QueryResponse } from './QueryResponse';

interface QueryHistoryProps {
  queries: Query[];
  onFollowUpClick?: (query: string) => void;
}

export const QueryHistory: React.FC<QueryHistoryProps> = ({
  queries,
  onFollowUpClick,
}) => {
  if (queries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 p-8">
        <svg
          className="w-16 h-16 mb-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          />
        </svg>
        <h3 className="text-lg font-medium mb-2">No queries yet</h3>
        <p className="text-sm text-center max-w-md">
          Start by asking a question about your APIs. Try asking about API health, predictions, or security vulnerabilities.
        </p>
        <div className="mt-6 space-y-2">
          <p className="text-xs font-medium text-gray-600">Example queries:</p>
          <ul className="text-xs space-y-1 text-gray-500">
            <li>• "Show me all critical vulnerabilities"</li>
            <li>• "What APIs have high error rates?"</li>
            <li>• "Are there any predictions for the next 24 hours?"</li>
            <li>• "Show me performance optimization recommendations"</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      {queries.map((query) => (
        <QueryResponse
          key={query.id}
          response={{
            query_id: query.id,
            query_text: query.query_text,
            response_text: query.response_text,
            confidence_score: query.confidence_score,
            results: query.results,
            follow_up_queries: query.follow_up_queries,
            execution_time_ms: query.execution_time_ms,
          }}
          onFollowUpClick={onFollowUpClick}
        />
      ))}
    </div>
  );
};

// Made with Bob
