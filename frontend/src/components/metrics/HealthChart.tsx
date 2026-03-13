import { LineChart } from '@carbon/charts-react';
import { ScaleTypes } from '@carbon/charts';
import '@carbon/charts-react/styles.css';
import Card from '../common/Card';
import type { TimeSeriesDataPoint } from '../../types';

/**
 * Health Metrics Chart Component
 * 
 * Displays time-series health metrics using Recharts:
 * - Response time (P50, P95, P99)
 * - Error rate
 * - Throughput
 * - Availability
 */

interface HealthChartProps {
  data: TimeSeriesDataPoint[];
  title?: string;
  subtitle?: string;
  metrics?: ('response_time' | 'error_rate' | 'throughput' | 'availability')[];
  height?: number;
}

const HealthChart = ({
  data,
  title = 'Health Metrics',
  subtitle = 'Time-series performance data',
  metrics = ['response_time', 'error_rate'],
  height = 300,
}: HealthChartProps) => {
  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  // Prepare data for Carbon Charts
  const chartData: any[] = [];
  
  data.forEach((point) => {
    const timestamp = formatTimestamp(point.timestamp);
    
    if (metrics.includes('response_time')) {
      chartData.push(
        { group: 'Response Time P50', date: timestamp, value: point.response_time_p50 },
        { group: 'Response Time P95', date: timestamp, value: point.response_time_p95 },
        { group: 'Response Time P99', date: timestamp, value: point.response_time_p99 }
      );
    }
    
    if (metrics.includes('error_rate')) {
      chartData.push({ group: 'Error Rate', date: timestamp, value: point.error_rate * 100 });
    }
    
    if (metrics.includes('throughput')) {
      chartData.push({ group: 'Throughput', date: timestamp, value: point.throughput });
    }
    
    if (metrics.includes('availability')) {
      chartData.push({ group: 'Availability', date: timestamp, value: point.availability });
    }
  });

  // Calculate summary statistics
  const calculateAverage = (metricName: string, getValue: (point: TimeSeriesDataPoint) => number) => {
    if (data.length === 0) return 0;
    return data.reduce((sum, point) => sum + getValue(point), 0) / data.length;
  };

  if (!data || data.length === 0) {
    return (
      <Card title={title} subtitle={subtitle}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '256px',
          color: 'var(--cds-text-secondary)'
        }}>
          No metrics data available
        </div>
      </Card>
    );
  }

  const options = {
    title: title,
    axes: {
      bottom: {
        title: 'Time',
        mapsTo: 'date',
        scaleType: ScaleTypes.LABELS,
      },
      left: {
        mapsTo: 'value',
        title: 'Value',
      },
    },
    height: `${height}px`,
    curve: 'curveMonotoneX',
    toolbar: {
      enabled: false,
    },
    legend: {
      enabled: true,
    },
  };

  return (
    <Card title={title} subtitle={subtitle}>
      <LineChart data={chartData} options={options} />

      {/* Summary Statistics */}
      <div style={{
        marginTop: 'var(--cds-spacing-05)',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: 'var(--cds-spacing-05)',
        paddingTop: 'var(--cds-spacing-05)',
        borderTop: '1px solid var(--cds-border-subtle)'
      }}>
        {metrics.includes('response_time') && (
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>
              Avg Response Time (P95)
            </p>
            <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
              {calculateAverage('response_time_p95', (p) => p.response_time_p95).toFixed(1)}ms
            </p>
          </div>
        )}
        {metrics.includes('error_rate') && (
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>
              Avg Error Rate
            </p>
            <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
              {(calculateAverage('error_rate', (p) => p.error_rate) * 100).toFixed(2)}%
            </p>
          </div>
        )}
        {metrics.includes('throughput') && (
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>
              Avg Throughput
            </p>
            <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
              {calculateAverage('throughput', (p) => p.throughput).toFixed(1)} req/s
            </p>
          </div>
        )}
        {metrics.includes('availability') && (
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>
              Avg Availability
            </p>
            <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>
              {calculateAverage('availability', (p) => p.availability).toFixed(2)}%
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default HealthChart;

// Made with Bob