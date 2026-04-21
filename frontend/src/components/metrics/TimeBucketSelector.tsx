import type { TimeBucket } from '../../types'

interface TimeBucketSelectorProps {
  value: TimeBucket
  onChange: (value: TimeBucket) => void
  label?: string
  className?: string
}

const timeBucketOptions: { value: TimeBucket; label: string; description: string }[] = [
  { value: '1m', label: '1 Minute', description: 'High-resolution recent activity' },
  { value: '5m', label: '5 Minutes', description: 'Balanced operational view' },
  { value: '1h', label: '1 Hour', description: 'Trend monitoring across the day' },
  { value: '1d', label: '1 Day', description: 'Long-range summary' },
]

const TimeBucketSelector = ({
  value,
  onChange,
  label = 'Time Bucket',
  className = '',
}: TimeBucketSelectorProps) => {
  return (
    <div className={className}>
      <label className="mb-1 block text-sm font-medium text-gray-700">{label}</label>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as TimeBucket)}
        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {timeBucketOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label} — {option.description}
          </option>
        ))}
      </select>
    </div>
  )
}

export default TimeBucketSelector

// Made with Bob
