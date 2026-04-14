import { useState } from 'react';
import { Clock } from 'lucide-react';

export type TimeRange = '1h' | '24h' | '7d' | '30d' | 'custom';

export interface TimeRangeValue {
  range: TimeRange;
  start?: Date;
  end?: Date;
}

interface TimeRangeSelectorProps {
  value: TimeRangeValue;
  onChange: (value: TimeRangeValue) => void;
  className?: string;
}

const TIME_RANGE_OPTIONS: { value: TimeRange; label: string }[] = [
  { value: '1h', label: 'Last Hour' },
  { value: '24h', label: 'Last 24 Hours' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: 'custom', label: 'Custom Range' },
];

/**
 * Time Range Selector Component
 * 
 * Allows users to select predefined time ranges or custom date ranges
 * for filtering dashboard and metrics data.
 */
const TimeRangeSelector = ({ value, onChange, className = '' }: TimeRangeSelectorProps) => {
  const [showCustom, setShowCustom] = useState(value.range === 'custom');

  const handleRangeChange = (range: TimeRange) => {
    if (range === 'custom') {
      setShowCustom(true);
      onChange({ range, start: value.start, end: value.end });
    } else {
      setShowCustom(false);
      const end = new Date();
      let start = new Date();
      
      switch (range) {
        case '1h':
          start.setHours(end.getHours() - 1);
          break;
        case '24h':
          start.setHours(end.getHours() - 24);
          break;
        case '7d':
          start.setDate(end.getDate() - 7);
          break;
        case '30d':
          start.setDate(end.getDate() - 30);
          break;
      }
      
      onChange({ range, start, end });
    }
  };

  const handleCustomDateChange = (type: 'start' | 'end', dateString: string) => {
    const date = new Date(dateString);
    onChange({
      range: 'custom',
      start: type === 'start' ? date : value.start,
      end: type === 'end' ? date : value.end,
    });
  };

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      <div className="flex items-center gap-2">
        <Clock className="w-4 h-4 text-gray-500" />
        <span className="text-sm font-medium text-gray-700">Time Range:</span>
      </div>
      
      <div className="flex flex-wrap gap-2">
        {TIME_RANGE_OPTIONS.map((option) => (
          <button
            key={option.value}
            onClick={() => handleRangeChange(option.value)}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
              value.range === option.value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {showCustom && (
        <div className="flex gap-3 items-center p-3 bg-gray-50 rounded-md">
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Start Date
            </label>
            <input
              type="datetime-local"
              value={value.start?.toISOString().slice(0, 16) || ''}
              onChange={(e) => handleCustomDateChange('start', e.target.value)}
              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-600 mb-1">
              End Date
            </label>
            <input
              type="datetime-local"
              value={value.end?.toISOString().slice(0, 16) || ''}
              onChange={(e) => handleCustomDateChange('end', e.target.value)}
              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default TimeRangeSelector;

// Made with Bob