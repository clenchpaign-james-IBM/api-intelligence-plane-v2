/**
 * Query Page
 *
 * Natural language query interface for API intelligence.
 * Provides a chat-like interface for asking questions about APIs.
 */

import React, { useState, useEffect, useRef } from 'react';
import { Heading, Button, Tag, InlineNotification } from '@carbon/react';
import { WarningAltFilled } from '@carbon/icons-react';
import { QueryHistory } from '../components/query/QueryHistory';
import { QueryInput } from '../components/query/QueryInput';
import { useQuerySession } from '../hooks/useQuerySession';
import Loading from '../components/common/Loading';
import Error from '../components/common/Error';

export const Query: React.FC = () => {
  const {
    sessionId,
    queries,
    isLoading,
    error,
    executeQuery,
    loadSessionHistory,
    clearSession,
  } = useQuerySession();

  const historyEndRef = useRef<HTMLDivElement>(null);

  // Load history on mount - only if session has queries
  useEffect(() => {
    console.log('[Query Page] Mount effect - sessionId:', sessionId, 'queries.length:', queries.length);
    if (sessionId && queries.length === 0) {
      // Only load if we don't have queries yet
      loadSessionHistory().catch((err) => {
        // Ignore errors on initial load (session might not exist yet)
        console.log('[Query Page] No existing session history');
      });
    }
  }, [sessionId]);

  // Auto-scroll to bottom when new queries arrive
  useEffect(() => {
    console.log('[Query Page] Queries updated, count:', queries.length);
    if (queries.length > 0) {
      console.log('[Query Page] Latest query:', queries[queries.length - 1]);
    }
    historyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [queries]);

  const handleSubmit = async (query: string) => {
    console.log('[Query Page] handleSubmit called with:', query);
    if (!query.trim()) return;
    console.log('[Query Page] Executing query...');
    await executeQuery(query);
    console.log('[Query Page] Query execution complete');
  };

  const handleFollowUpClick = async (query: string) => {
    console.log('[Query Page] Follow-up clicked:', query);
    await handleSubmit(query);
  };

  const handleClearSession = () => {
    if (window.confirm('Are you sure you want to clear the conversation history?')) {
      clearSession();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: 'var(--cds-layer-01)' }}>
      {/* Header */}
      <div style={{
        backgroundColor: 'var(--cds-background)',
        borderBottom: '1px solid var(--cds-border-subtle)',
        padding: 'var(--cds-spacing-06)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <Heading style={{ marginBottom: 'var(--cds-spacing-02)' }}>
              Natural Language Query
            </Heading>
            <p style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>
              Ask questions about your APIs in plain English
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-04)' }}>
            {sessionId && (
              <Tag type="gray" size="sm">
                Session: {sessionId.slice(0, 8)}...
              </Tag>
            )}
            {queries.length > 0 && (
              <Button
                kind="danger--ghost"
                size="sm"
                onClick={handleClearSession}
              >
                Clear History
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, overflowY: 'auto', position: 'relative' }}>
        {error && (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 'var(--cds-spacing-07)' }}>
            <div style={{
              maxWidth: '28rem',
              width: '100%',
              padding: 'var(--cds-spacing-07)'
            }}>
              <InlineNotification
                kind="error"
                title="Connection Error"
                subtitle="Unable to connect to the backend server. Please make sure the server is running."
                lowContrast
              >
                <div style={{
                  backgroundColor: 'var(--cds-background)',
                  borderRadius: 'var(--cds-spacing-02)',
                  padding: 'var(--cds-spacing-04)',
                  marginTop: 'var(--cds-spacing-04)',
                  marginBottom: 'var(--cds-spacing-04)'
                }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)', fontFamily: 'monospace' }}>{error}</p>
                </div>
                <Button
                  kind="danger"
                  size="sm"
                  onClick={() => window.location.reload()}
                >
                  Retry Connection
                </Button>
              </InlineNotification>
            </div>
          </div>
        )}

        <QueryHistory
          queries={queries}
          onFollowUpClick={handleFollowUpClick}
        />

        {isLoading && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--cds-spacing-05)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-03)', color: 'var(--cds-text-secondary)' }}>
              <Loading size="sm" />
              <span style={{ fontSize: '0.875rem' }}>Processing your query...</span>
            </div>
          </div>
        )}

        {/* Help Section - shown when no queries */}
        {queries.length === 0 && !isLoading && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--cds-spacing-05)' }}>
            <div style={{ width: '100%', maxWidth: '42rem' }}>
              <InlineNotification
                kind="info"
                title="💡 Tips for better results:"
                subtitle=""
                lowContrast
                hideCloseButton
              >
                <ul style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)', paddingLeft: 'var(--cds-spacing-05)', marginTop: 'var(--cds-spacing-03)' }}>
                  <li>Be specific about what you want to know</li>
                  <li>Use natural language - no need for technical syntax</li>
                  <li>Ask follow-up questions to dive deeper</li>
                  <li>Try asking about health, performance, security, or predictions</li>
                </ul>
              </InlineNotification>
            </div>
          </div>
        )}

        <div ref={historyEndRef} />
      </div>

      {/* Input Area */}
      <QueryInput
        onSubmit={handleSubmit}
        isLoading={isLoading}
        placeholder="Ask a question about your APIs..."
      />

    </div>
  );
};

// Made with Bob
