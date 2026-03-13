import { SimpleBarChart } from '@carbon/charts-react';
import { ScaleTypes } from '@carbon/charts';
import '@carbon/charts-react/styles.css';
import type { ContributingFactor } from '../../types';

interface FactorsChartProps {
  factors: ContributingFactor[];
}

/**
 * Factors Chart Component
 * 
 * Visualizes contributing factors using Recharts:
 * - Bar chart showing factor weights
 * - Color-coded by trend direction
 * - Tooltip with detailed information
 */
const FactorsChart = ({ factors }: FactorsChartProps) => {
  // Prepare data for Carbon Charts
  const chartData = factors
    .map((factor) => ({
      group: factor.factor.replace(/_/g, ' ').slice(0, 20),
      value: factor.weight * 100,
      trend: factor.trend,
    }))
    .sort((a, b) => b.value - a.value);

  // Color palette based on trend
  const colorPalette = {
    increasing: '#da1e28', // Carbon red
    decreasing: '#24a148', // Carbon green
    stable: '#8d8d8d', // Carbon gray
    volatile: '#f1c21b', // Carbon yellow
  };

  if (factors.length === 0) {
    return (
      <div style={{
        textAlign: 'center',
        padding: 'var(--cds-spacing-05)',
        color: 'var(--cds-text-secondary)'
      }}>
        No contributing factors available
      </div>
    );
  }

  const options = {
    title: 'Contributing Factors',
    axes: {
      left: {
        title: 'Weight (%)',
        mapsTo: 'value',
      },
      bottom: {
        title: 'Factor',
        mapsTo: 'group',
        scaleType: ScaleTypes.LABELS,
      },
    },
    height: '300px',
    toolbar: {
      enabled: false,
    },
    legend: {
      enabled: true,
    },
    color: {
      scale: colorPalette,
    },
  };

  return (
    <div style={{ width: '100%' }}>
      <SimpleBarChart data={chartData} options={options} />
      
      {/* Legend */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 'var(--cds-spacing-05)',
        marginTop: 'var(--cds-spacing-03)',
        fontSize: '0.75rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-02)' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: '#da1e28' }} />
          <span style={{ color: 'var(--cds-text-secondary)' }}>Increasing</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-02)' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: '#24a148' }} />
          <span style={{ color: 'var(--cds-text-secondary)' }}>Decreasing</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-02)' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: '#8d8d8d' }} />
          <span style={{ color: 'var(--cds-text-secondary)' }}>Stable</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cds-spacing-02)' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: '#f1c21b' }} />
          <span style={{ color: 'var(--cds-text-secondary)' }}>Volatile</span>
        </div>
      </div>
    </div>
  );
};

export default FactorsChart;

// Made with Bob