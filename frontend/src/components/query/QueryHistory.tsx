/**
 * Query History Component
 *
 * Displays conversation history with queries and responses.
 */

import React from 'react';
import { Chat } from '@carbon/icons-react';
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
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        color: 'var(--cds-text-secondary)',
        padding: 'var(--cds-spacing-07)'
      }}>
        <Chat size={64} style={{ marginBottom: 'var(--cds-spacing-05)', color: 'var(--cds-icon-disabled)' }} />
        <h3 style={{ fontSize: '1.125rem', fontWeight: 500, marginBottom: 'var(--cds-spacing-03)', color: 'var(--cds-text-primary)' }}>
          No queries yet
        </h3>
        <p style={{ fontSize: '0.875rem', textAlign: 'center', maxWidth: '28rem', color: 'var(--cds-text-secondary)' }}>
          Start by asking a question about your APIs. Try asking about API health, predictions, or security vulnerabilities.
        </p>
        <div style={{ marginTop: 'var(--cds-spacing-07)', display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-03)' }}>
          <p style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--cds-text-secondary)' }}>Example queries:</p>
          <ul style={{ fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-02)', color: 'var(--cds-text-secondary)', listStyle: 'none', paddingLeft: 0 }}>
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cds-spacing-07)', padding: 'var(--cds-spacing-05)' }}>
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
