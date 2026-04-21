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
  createNewSession: () => Promise<void>;
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

      console.log('[useQuerySession] Loading history for session:', targetSessionId);
      const response = await api.get(`/api/v1/query/session/${targetSessionId}`);
      console.log('[useQuerySession] History response:', response);
      console.log('[useQuerySession] Items:', response.items);
      
      // api.get already returns response.data, so response is the QueryHistoryResponse
      setQueries(response.items || []);
      console.log('[useQuerySession] Queries state updated, count:', response.items?.length || 0);
    } catch (err: any) {
      console.error('[useQuerySession] Failed to load session history:', err);
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

    // Generate a temporary ID for the query
    const tempQueryId = `temp-${Date.now()}`;
    
    // Create a pending query object and add it to state immediately
    const pendingQuery: Query = {
      id: tempQueryId,
      session_id: sessionId,
      user_id: undefined,
      query_text: queryText,
      query_type: 'general' as any,
      interpreted_intent: undefined as any,
      opensearch_query: undefined,
      results: undefined as any,
      response_text: '', // Empty response initially - will be filled when backend responds
      confidence_score: 0, // Default value for pending query
      execution_time_ms: 0, // Default value for pending query
      feedback: undefined,
      feedback_comment: undefined,
      follow_up_queries: [],
      metadata: undefined,
      created_at: new Date().toISOString(),
    };

    console.log('[useQuerySession] Adding pending query to state:', pendingQuery);
    setQueries((prev: Query[]) => [...prev, pendingQuery]);

    try {
      setIsLoading(true);
      setError(null);

      const request: QueryRequest = {
        query_text: queryText,
        session_id: sessionId,
      };

      console.log('[useQuerySession] Executing query:', queryText);
      console.log('[useQuerySession] Request:', request);
      
      const response = await api.post<QueryResponse>('/api/v1/query', request);
      console.log('[useQuerySession] Query response:', response);
      
      // Update the pending query with the actual response
      const completedQuery: Query = {
        id: response.query_id,
        session_id: sessionId,
        user_id: undefined,
        query_text: response.query_text,
        query_type: 'general' as any,
        interpreted_intent: undefined as any,
        opensearch_query: undefined,
        results: response.results as any,
        response_text: response.response_text,
        confidence_score: response.confidence_score,
        execution_time_ms: response.execution_time_ms,
        feedback: undefined,
        feedback_comment: undefined,
        follow_up_queries: response.follow_up_queries || [],
        metadata: undefined,
        created_at: new Date().toISOString(),
      };
      
      console.log('[useQuerySession] Updating query with response:', completedQuery);
      // Replace the pending query with the completed one
      setQueries((prev: Query[]) =>
        prev.map(q => q.id === tempQueryId ? completedQuery : q)
      );
      console.log('[useQuerySession] Query updated with response');

      return response;
    } catch (err: any) {
      console.error('[useQuerySession] Failed to execute query:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to execute query';
      setError(errorMessage);
      
      // Update the pending query with error state
      setQueries((prev: Query[]) =>
        prev.map(q => q.id === tempQueryId ? {
          ...q,
          response_text: `Error: ${errorMessage}`,
        } : q)
      );
      
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

  /**
   * Create a new session via backend API
   */
  const createNewSession = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      console.log('[useQuerySession] Creating new session via API');
      const response = await api.post<{ session_id: string; created_at: string }>(
        '/api/v1/query/session/new',
        {}
      );
      
      const newSessionId = response.session_id;
      console.log('[useQuerySession] New session created:', newSessionId);
      
      setSessionId(newSessionId);
      setQueries([]);
      localStorage.setItem('query_session_id', newSessionId);
    } catch (err: any) {
      console.error('[useQuerySession] Failed to create new session:', err);
      // Fallback to local session generation
      console.log('[useQuerySession] Falling back to local session generation');
      clearSession();
    } finally {
      setIsLoading(false);
    }
  }, [clearSession]);

  return {
    sessionId,
    queries,
    isLoading,
    error,
    executeQuery,
    clearSession,
    createNewSession,
    loadSessionHistory,
  };
};

// Made with Bob
