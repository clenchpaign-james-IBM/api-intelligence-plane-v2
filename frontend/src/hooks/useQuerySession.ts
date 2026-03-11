/**
 * Query Session Management Hook
 * 
 * Manages conversation context and session state for natural language queries.
 * Provides session creation, query history, and context preservation.
 */

import { useState, useEffect, useCallback } from 'react';
import { Query, QueryRequest, QueryResponse } from '../types';
import { api } from '../services/api';

// Simple UUID v4 generator
const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

interface UseQuerySessionReturn {
  sessionId: string;
  queries: Query[];
  isLoading: boolean;
  error: string | null;
  executeQuery: (queryText: string) => Promise<QueryResponse | null>;
  clearSession: () => void;
  loadSessionHistory: () => Promise<void>;
}

/**
 * Hook for managing query sessions and conversation context
 */
export const useQuerySession = (): UseQuerySessionReturn => {
  const [sessionId, setSessionId] = useState<string>('');
  const [queries, setQueries] = useState<Query[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize or restore session on mount
  useEffect(() => {
    const storedSessionId = localStorage.getItem('query_session_id');
    if (storedSessionId) {
      setSessionId(storedSessionId);
      // Load session history
      loadSessionHistory(storedSessionId);
    } else {
      // Create new session
      const newSessionId = generateUUID();
      setSessionId(newSessionId);
      localStorage.setItem('query_session_id', newSessionId);
    }
  }, []);

  /**
   * Load query history for current session
   */
  const loadSessionHistory = useCallback(async (sid?: string) => {
    const targetSessionId = sid || sessionId;
    if (!targetSessionId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await api.get(`/api/v1/query/session/${targetSessionId}`);
      setQueries(response.data.items || []);
    } catch (err: any) {
      console.error('Failed to load session history:', err);
      setError(err.message || 'Failed to load session history');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  /**
   * Execute a natural language query
   */
  const executeQuery = useCallback(async (queryText: string): Promise<QueryResponse | null> => {
    if (!queryText.trim()) {
      setError('Query text cannot be empty');
      return null;
    }

    try {
      setIsLoading(true);
      setError(null);

      const request: QueryRequest = {
        query_text: queryText,
        session_id: sessionId,
      };

      const response = await api.post<QueryResponse>('/api/v1/query', request);
      
      // Reload session history to get the new query
      await loadSessionHistory();

      return response;
    } catch (err: any) {
      console.error('Failed to execute query:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to execute query';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, loadSessionHistory]);

  /**
   * Clear current session and start a new one
   */
  const clearSession = useCallback(() => {
    const newSessionId = generateUUID();
    setSessionId(newSessionId);
    setQueries([]);
    setError(null);
    localStorage.setItem('query_session_id', newSessionId);
  }, []);

  return {
    sessionId,
    queries,
    isLoading,
    error,
    executeQuery,
    clearSession,
    loadSessionHistory,
  };
};

// Made with Bob
