import type { TimeBucket } from '../../types'

interface TimeBucketSelectorProps {
  value: TimeBucket
  onChange: (value: TimeBucket) => void
  className?: string
}

const TIME_BUCKET_OPTIONS: Array<{ value: TimeBucket; label: string }> = [
  { value: '1m', label: '1 Minute' },
  { value: '5m', label: '5 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '1d', label: '1 Day' },
]

const TimeBucketSelector = ({
  value,
  onChange,
  className = '',
}: TimeBucketSelectorProps) => {
  return (
    <div className={className}>
      <label
        htmlFor="time-bucket-selector"
        className="block text-sm font-medium text-gray-700 mb-2"
      >
        Time Bucket
      </label>
      <select
        id="time-bucket-selector"
        value={value}
        onChange={(event) => onChange(event.target.value as TimeBucket)}
        className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      >
        {TIME_BUCKET_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export default TimeBucketSelector

// Made with Bob
