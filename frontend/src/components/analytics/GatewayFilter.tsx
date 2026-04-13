import type { Gateway } from '../../types'

interface GatewayFilterProps {
  gateways: Gateway[]
  value?: string
  onChange: (gatewayId?: string) => void
  className?: string
}

const GatewayFilter = ({
  gateways,
  value,
  onChange,
  className = '',
}: GatewayFilterProps) => {
  return (
    <div className={className}>
      <label
        htmlFor="gateway-filter"
        className="block text-sm font-medium text-gray-700 mb-2"
      >
        Gateway
      </label>
      <select
        id="gateway-filter"
        value={value ?? ''}
        onChange={(event) =>
          onChange(event.target.value ? event.target.value : undefined)
        }
        className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      >
        <option value="">All Gateways</option>
        {gateways.map((gateway) => (
          <option key={gateway.id} value={gateway.id}>
            {gateway.name}
          </option>
        ))}
      </select>
    </div>
  )
}

export default GatewayFilter

// Made with Bob
