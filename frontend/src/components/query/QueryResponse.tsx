/**
 * Query Response Component
 *
 * Displays AI-generated response with confidence score and follow-up suggestions.
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Tag, Button } from '@carbon/react';
import { Flash, CheckmarkFilled, Document } from '@carbon/icons-react';
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
  const getConfidenceTagType = (score: number): 'green' | 'warm-gray' | 'red' => {
    if (score >= 0.8) return 'green';
    if (score >= 0.6) return 'warm-gray';
    return 'red';
  };

  const getConfidenceLabel = (score: number): string => {
    if (score >= 0.8) return 'High';
    if (score >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-05)' }}>
      {/* User Query */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <div style={{
          maxWidth: '80%',
          backgroundColor: 'var(--cds-link-primary)',
          color: 'var(--cds-text-on-color)',
          borderRadius: 'var(--cds-spacing-03)',
          padding: 'var(--cds-spacing-05)'
        }}>
          <p style={{ fontSize: '0.875rem', margin: 0 }}>{response.query_text}</p>
        </div>
      </div>

      {/* AI Response */}
      <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
        <div style={{ maxWidth: '80%', width: '100%' }}>
          <Card>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-05)' }}>
              {/* Response Text with Markdown */}
              <div style={{
                fontSize: '0.875rem',
                lineHeight: 1.6,
                color: 'var(--cds-text-primary)'
              }}>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({node, ...props}) => <h1 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: 'var(--cds-spacing-04)', color: 'var(--cds-text-primary)' }} {...props} />,
                    h2: ({node, ...props}) => <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: 'var(--cds-spacing-03)', color: 'var(--cds-text-primary)' }} {...props} />,
                    h3: ({node, ...props}) => <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: 'var(--cds-spacing-03)', color: 'var(--cds-text-primary)' }} {...props} />,
                    p: ({node, ...props}) => <p style={{ marginBottom: 'var(--cds-spacing-04)', color: 'var(--cds-text-primary)' }} {...props} />,
                    a: ({node, ...props}) => <a style={{ color: 'var(--cds-link-primary)', textDecoration: 'underline' }} {...props} />,
                    code: ({node, inline, ...props}: any) => inline
                      ? <code style={{ backgroundColor: 'var(--cds-layer-01)', padding: '2px 6px', borderRadius: '4px', fontFamily: 'monospace', fontSize: '0.875em' }} {...props} />
                      : <code style={{ display: 'block', backgroundColor: 'var(--cds-layer-01)', padding: 'var(--cds-spacing-04)', borderRadius: 'var(--cds-spacing-02)', fontFamily: 'monospace', fontSize: '0.875em', overflowX: 'auto' }} {...props} />,
                    ul: ({node, ...props}) => <ul style={{ marginLeft: 'var(--cds-spacing-06)', marginBottom: 'var(--cds-spacing-04)' }} {...props} />,
                    ol: ({node, ...props}) => <ol style={{ marginLeft: 'var(--cds-spacing-06)', marginBottom: 'var(--cds-spacing-04)' }} {...props} />,
                    li: ({node, ...props}) => <li style={{ marginBottom: 'var(--cds-spacing-02)' }} {...props} />,
                  }}
                >
                  {response.response_text}
                </ReactMarkdown>
              </div>

              {/* Metadata */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--cds-spacing-05)',
                fontSize: '0.75rem',
                color: 'var(--cds-text-secondary)',
                borderTop: '1px solid var(--cds-border-subtle)',
                paddingTop: 'var(--cds-spacing-04)',
                flexWrap: 'wrap'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-02)' }}>
                  <Flash size={16} />
                  <span>{response.execution_time_ms}ms</span>
                </div>
                <Tag type={getConfidenceTagType(response.confidence_score)} size="sm">
                  {getConfidenceLabel(response.confidence_score)} ({Math.round(response.confidence_score * 100)}%)
                </Tag>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-02)' }}>
                  <Document size={16} />
                  <span>{response.results.count} results</span>
                </div>
              </div>

              {/* Follow-up Suggestions */}
              {response.follow_up_queries && response.follow_up_queries.length > 0 && (
                <div style={{ borderTop: '1px solid var(--cds-border-subtle)', paddingTop: 'var(--cds-spacing-04)' }}>
                  <p style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--cds-text-secondary)', marginBottom: 'var(--cds-spacing-03)' }}>
                    Suggested follow-ups:
                  </p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--cds-spacing-03)' }}>
                    {response.follow_up_queries.map((query, index) => (
                      <Button
                        key={index}
                        kind="ghost"
                        size="sm"
                        onClick={() => onFollowUpClick?.(query)}
                      >
                        {query}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

// Made with Bob
