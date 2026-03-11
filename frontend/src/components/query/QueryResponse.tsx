/**
 * Query Response Component
 * 
 * Displays AI-generated response with confidence score and follow-up suggestions.
 */

import React from 'react';
import { QueryResponse as QueryResponseType } from '../../types';
import { Card } from '../common';

interface QueryResponseProps {
  response: QueryResponseType;
  onFollowUpClick?: (query: string) => void;
}

export const QueryResponse: React.FC<QueryResponseProps> = ({
  response,
  onFollowUpClick,
}) => {
  const getConfidenceColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceLabel = (score: number): string => {
    if (score >= 0.8) return 'High';
    if (score >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <div className="space-y-4">
      {/* User Query */}
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-blue-600 text-white rounded-lg px-4 py-3">
          <p className="text-sm">{response.query_text}</p>
        </div>
      </div>

      {/* AI Response */}
      <div className="flex justify-start">
        <Card className="max-w-[80%]">
          <div className="space-y-4">
            {/* Response Text */}
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-800 whitespace-pre-wrap">{response.response_text}</p>
            </div>

            {/* Metadata */}
            <div className="flex items-center gap-4 text-xs text-gray-500 border-t pt-3">
              <div className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
                <span>{response.execution_time_ms}ms</span>
              </div>
              <div className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span className={getConfidenceColor(response.confidence_score)}>
                  {getConfidenceLabel(response.confidence_score)} Confidence ({Math.round(response.confidence_score * 100)}%)
                </span>
              </div>
              <div className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                  />
                </svg>
                <span>{response.results.count} results</span>
              </div>
            </div>

            {/* Follow-up Suggestions */}
            {response.follow_up_queries && response.follow_up_queries.length > 0 && (
              <div className="border-t pt-3">
                <p className="text-xs font-medium text-gray-700 mb-2">Suggested follow-ups:</p>
                <div className="flex flex-wrap gap-2">
                  {response.follow_up_queries.map((query, index) => (
                    <button
                      key={index}
                      onClick={() => onFollowUpClick?.(query)}
                      className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
                    >
                      {query}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

// Made with Bob
