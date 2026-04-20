/**
 * Query Response Component
 *
 * Displays AI-generated response with confidence score and follow-up suggestions.
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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
            {/* Response Text with Markdown */}
            <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-800 prose-a:text-blue-600 prose-strong:text-gray-900 prose-code:text-gray-800 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-100 prose-pre:text-gray-800">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {response.response_text}
              </ReactMarkdown>
            </div>

            {/* AI Agent Insights - Security */}
            {response.results?.data?.some((item: any) => item.agent_insights?.type === 'security') && (
              <div className="border-t pt-3">
                <div className="flex items-center gap-2 mb-3">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span className="text-sm font-semibold text-purple-900">🔒 AI Security Analysis</span>
                </div>
                {response.results.data
                  .filter((item: any) => item.agent_insights?.type === 'security')
                  .slice(0, 2)
                  .map((item: any, idx: number) => (
                    <div key={idx} className="bg-purple-50 rounded-lg p-3 mb-2">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-purple-900">{item.name}</span>
                        <div className="flex items-center gap-2">
                          {item.agent_insights.critical_count > 0 && (
                            <span className="text-xs px-2 py-1 bg-red-100 text-red-800 rounded-full font-medium">
                              {item.agent_insights.critical_count} Critical
                            </span>
                          )}
                          <span className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                            {item.agent_insights.total_vulnerabilities} Issues
                          </span>
                        </div>
                      </div>
                      {item.agent_insights.remediation_plan && (
                        <div className="text-xs text-purple-700 space-y-1">
                          {typeof item.agent_insights.remediation_plan === 'string' ? (
                            <p className="line-clamp-2">{item.agent_insights.remediation_plan.substring(0, 150)}...</p>
                          ) : (
                            <>
                              {item.agent_insights.remediation_plan.priority && (
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">Priority:</span>
                                  <span className={`px-2 py-0.5 rounded text-xs ${
                                    item.agent_insights.remediation_plan.priority === 'critical' ? 'bg-red-100 text-red-800' :
                                    item.agent_insights.remediation_plan.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                                    item.agent_insights.remediation_plan.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-blue-100 text-blue-800'
                                  }`}>
                                    {item.agent_insights.remediation_plan.priority.toUpperCase()}
                                  </span>
                                </div>
                              )}
                              {item.agent_insights.remediation_plan.actions && item.agent_insights.remediation_plan.actions.length > 0 && (
                                <p className="line-clamp-2">
                                  {item.agent_insights.remediation_plan.actions[0].action}
                                  {item.agent_insights.remediation_plan.actions.length > 1 && ` (+${item.agent_insights.remediation_plan.actions.length - 1} more)`}
                                </p>
                              )}
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            )}

            {/* AI Agent Insights - Predictions */}
            {response.results?.data?.some((item: any) => item.agent_insights?.type === 'prediction') && (
              <div className="border-t pt-3">
                <div className="flex items-center gap-2 mb-3">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span className="text-sm font-semibold text-blue-900">🔮 AI Prediction Insights</span>
                </div>
                {response.results.data
                  .filter((item: any) => item.agent_insights?.type === 'prediction')
                  .slice(0, 2)
                  .map((item: any, idx: number) => (
                    <div key={idx} className="bg-blue-50 rounded-lg p-3 mb-2">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-blue-900">{item.name}</span>
                        <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                          {item.agent_insights.predictions?.length || 0} Predictions
                        </span>
                      </div>
                      {item.agent_insights.analysis && (
                        <p className="text-xs text-blue-700 line-clamp-2">
                          {item.agent_insights.analysis.substring(0, 150)}...
                        </p>
                      )}
                    </div>
                  ))}
              </div>
            )}

            {/* AI Agent Insights - Optimization */}
            {response.results?.data?.some((item: any) => item.agent_insights?.type === 'optimization') && (
              <div className="border-t pt-3">
                <div className="flex items-center gap-2 mb-3">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  <span className="text-sm font-semibold text-green-900">⚡ AI Performance Insights</span>
                </div>
                {response.results.data
                  .filter((item: any) => item.agent_insights?.type === 'optimization')
                  .slice(0, 2)
                  .map((item: any, idx: number) => (
                    <div key={idx} className="bg-green-50 rounded-lg p-3 mb-2">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-green-900">{item.name}</span>
                        <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">
                          {item.agent_insights.recommendations?.length || 0} Recommendations
                        </span>
                      </div>
                      {item.agent_insights.performance_analysis && (
                        <p className="text-xs text-green-700 line-clamp-2">
                          {item.agent_insights.performance_analysis.substring(0, 150)}...
                        </p>
                      )}
                    </div>
                  ))}
              </div>
            )}

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
