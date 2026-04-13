import { useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { metricsService } from '../services/metrics';
import type { Metric, MetricsTimeSeriesResponse } from '../types';

/**
 * Hook for real-time metrics updates using polling.
 * 
 * This implementation uses polling as a fallback. For production,
 * consider implementing WebSocket or SSE on the backend for true real-time updates.
 */

interface UseRealtimeMetricsOptions {
  apiId: string;
  enabled?: boolean;
  pollingInterval?: number; // milliseconds, default 5000 (5 seconds)
  onUpdate?: (metrics: Metric) => void;
  onError?: (error: Error) => void;
}

export function useRealtimeMetrics({
  apiId,
  enabled = true,
  pollingInterval = 5000,
  onUpdate,
  onError,
}: UseRealtimeMetricsOptions) {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const previousMetricsRef = useRef<Metric | null>(null);

  // Query for current metrics with polling
  const { data: metrics, error, isLoading } = useQuery({
    queryKey: ['metrics', 'realtime', apiId],
    queryFn: () => metricsService.getCurrent(apiId),
    enabled: enabled && !!apiId,
    refetchInterval: enabled ? pollingInterval : false,
    refetchIntervalInBackground: true,
    staleTime: 0, // Always consider data stale to ensure fresh fetches
  });

  // Track connection status
  useEffect(() => {
    if (enabled && !error) {
      setIsConnected(true);
    } else {
      setIsConnected(false);
    }
  }, [enabled, error]);

  // Handle metrics updates
  useEffect(() => {
    if (metrics && metrics !== previousMetricsRef.current) {
      setLastUpdate(new Date());
      previousMetricsRef.current = metrics;
      
      if (onUpdate) {
        onUpdate(metrics);
      }

      // Invalidate related queries to keep UI in sync
      queryClient.invalidateQueries({ queryKey: ['apis', apiId] });
    }
  }, [metrics, apiId, onUpdate, queryClient]);

  // Handle errors
  useEffect(() => {
    if (error && onError) {
      onError(error as Error);
    }
  }, [error, onError]);

  return {
    metrics,
    isLoading,
    error,
    isConnected,
    lastUpdate,
  };
}

/**
 * Hook for real-time time-series metrics updates.
 * Useful for live charts and graphs.
 */
interface UseRealtimeTimeSeriesOptions {
  apiId: string;
  start?: string;
  end?: string;
  interval?: number;
  enabled?: boolean;
  pollingInterval?: number;
  onUpdate?: (data: MetricsTimeSeriesResponse) => void;
}

export function useRealtimeTimeSeries({
  apiId,
  start,
  end,
  interval,
  enabled = true,
  pollingInterval = 10000, // 10 seconds for time series
  onUpdate,
}: UseRealtimeTimeSeriesOptions) {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const { data, error, isLoading } = useQuery({
    queryKey: ['metrics', 'timeseries', 'realtime', apiId, start, end, interval],
    queryFn: () => metricsService.getTimeSeries(apiId, { start, end, interval }),
    enabled: enabled && !!apiId,
    refetchInterval: enabled ? pollingInterval : false,
    refetchIntervalInBackground: true,
    staleTime: 0,
  });

  useEffect(() => {
    if (data) {
      setLastUpdate(new Date());
      if (onUpdate) {
        onUpdate(data);
      }
    }
  }, [data, onUpdate]);

  return {
    data,
    isLoading,
    error,
    lastUpdate,
  };
}

/**
 * Hook for monitoring multiple APIs in real-time.
 * Useful for dashboard views.
 */
interface UseRealtimeMultipleMetricsOptions {
  apiIds: string[];
  enabled?: boolean;
  pollingInterval?: number;
  onUpdate?: (apiId: string, metrics: Metric) => void;
}

export function useRealtimeMultipleMetrics({
  apiIds,
  enabled = true,
  pollingInterval = 5000,
  onUpdate,
}: UseRealtimeMultipleMetricsOptions) {
  const [metricsMap, setMetricsMap] = useState<Map<string, Metric>>(new Map());
  const [errors, setErrors] = useState<Map<string, Error>>(new Map());
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Use individual queries for each API
  // This would typically use useQueries from React Query
  // For simplicity, we'll track updates manually
  useEffect(() => {
    if (!enabled) return;

    const fetchAll = async () => {
      const newMetricsMap = new Map<string, Metric>();
      const newErrorsMap = new Map<string, Error>();

      await Promise.allSettled(
        apiIds.map(async (apiId) => {
          try {
            const metrics = await metricsService.getCurrent(apiId);
            if (metrics) {
              newMetricsMap.set(apiId, metrics);
              if (onUpdate) {
                onUpdate(apiId, metrics);
              }
            }
          } catch (error) {
            newErrorsMap.set(apiId, error as Error);
          }
        })
      );

      setMetricsMap(newMetricsMap);
      setErrors(newErrorsMap);
      setLastUpdate(new Date());
    };

    fetchAll();
    const intervalId = setInterval(fetchAll, pollingInterval);

    return () => clearInterval(intervalId);
  }, [apiIds, enabled, pollingInterval, onUpdate]);

  return {
    metricsMap,
    errors,
    lastUpdate,
    isLoading: metricsMap.size === 0 && errors.size === 0,
  };
}

/**
 * Hook for subscribing to metrics alerts/notifications.
 * Monitors for threshold breaches and anomalies.
 */
interface UseMetricsAlertsOptions {
  apiId: string;
  thresholds?: {
    responseTimeP95?: number; // ms
    errorRate?: number; // percentage
    availability?: number; // percentage
  };
  enabled?: boolean;
  pollingInterval?: number;
  onAlert?: (alert: MetricsAlert) => void;
}

export interface MetricsAlert {
  apiId: string;
  metric: string;
  value: number;
  threshold: number;
  severity: 'warning' | 'critical';
  timestamp: Date;
}

export function useMetricsAlerts({
  apiId,
  thresholds = {},
  enabled = true,
  pollingInterval = 5000,
  onAlert,
}: UseMetricsAlertsOptions) {
  const [alerts, setAlerts] = useState<MetricsAlert[]>([]);
  const previousMetricsRef = useRef<Metric | null>(null);

  const { metrics } = useRealtimeMetrics({
    apiId,
    enabled,
    pollingInterval,
  });

  useEffect(() => {
    if (!metrics || !enabled) return;

    const newAlerts: MetricsAlert[] = [];

    // Check response time threshold
    if (thresholds.responseTimeP95 && metrics.response_time_p95 > thresholds.responseTimeP95) {
      const alert: MetricsAlert = {
        apiId,
        metric: 'response_time_p95',
        value: metrics.response_time_p95,
        threshold: thresholds.responseTimeP95,
        severity: metrics.response_time_p95 > thresholds.responseTimeP95 * 1.5 ? 'critical' : 'warning',
        timestamp: new Date(),
      };
      newAlerts.push(alert);
      if (onAlert) onAlert(alert);
    }

    const totalRequests = metrics.request_count ?? 0;
    const errorCount = (metrics.status_4xx_count ?? 0) + (metrics.status_5xx_count ?? 0);
    const successCount = metrics.success_count ?? Math.max(totalRequests - errorCount, 0);
    const computedErrorRate = totalRequests > 0 ? (errorCount / totalRequests) * 100 : 0;
    const computedAvailability = totalRequests > 0 ? (successCount / totalRequests) * 100 : 100;

    // Check error rate threshold
    if (thresholds.errorRate && computedErrorRate > thresholds.errorRate) {
      const alert: MetricsAlert = {
        apiId,
        metric: 'error_rate',
        value: computedErrorRate,
        threshold: thresholds.errorRate,
        severity: computedErrorRate > thresholds.errorRate * 2 ? 'critical' : 'warning',
        timestamp: new Date(),
      };
      newAlerts.push(alert);
      if (onAlert) onAlert(alert);
    }

    // Check availability threshold
    if (thresholds.availability && computedAvailability < thresholds.availability) {
      const alert: MetricsAlert = {
        apiId,
        metric: 'availability',
        value: computedAvailability,
        threshold: thresholds.availability,
        severity: computedAvailability < thresholds.availability * 0.9 ? 'critical' : 'warning',
        timestamp: new Date(),
      };
      newAlerts.push(alert);
      if (onAlert) onAlert(alert);
    }

    if (newAlerts.length > 0) {
      setAlerts((prev: MetricsAlert[]) => [...newAlerts, ...prev].slice(0, 100)); // Keep last 100 alerts
    }

    previousMetricsRef.current = metrics;
  }, [metrics, thresholds, apiId, enabled, onAlert]);

  return {
    alerts,
    clearAlerts: () => setAlerts([]),
  };
}

// Made with Bob
