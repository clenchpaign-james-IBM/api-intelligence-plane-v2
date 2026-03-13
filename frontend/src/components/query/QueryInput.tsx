/**
 * Query Input Component
 *
 * Text input for natural language queries with send button and loading state.
 */

import React, { useState, KeyboardEvent } from 'react';
import { TextArea, Button } from '@carbon/react';
import { SendAlt, InProgress } from '@carbon/icons-react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export const QueryInput: React.FC<QueryInputProps> = ({
  onSubmit,
  isLoading,
  placeholder = 'Ask a question about your APIs...',
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = () => {
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
      setQuery('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div style={{
      padding: 'var(--cds-spacing-05)',
      backgroundColor: 'var(--cds-background)',
      borderTop: '1px solid var(--cds-border-subtle)'
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 'var(--cds-spacing-03)' }}>
        <div style={{ flex: 1 }}>
          <TextArea
            id="query-input"
            labelText=""
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={isLoading}
            rows={3}
            style={{ resize: 'none' }}
          />
        </div>
        <Button
          kind="primary"
          onClick={handleSubmit}
          disabled={!query.trim() || isLoading}
          renderIcon={isLoading ? InProgress : SendAlt}
          style={{ flexShrink: 0 }}
        >
          {isLoading ? 'Thinking...' : 'Send'}
        </Button>
      </div>
      <div style={{
        marginTop: 'var(--cds-spacing-03)',
        fontSize: '0.875rem',
        color: 'var(--cds-text-secondary)',
        textAlign: 'center'
      }}>
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  );
};

// Made with Bob
