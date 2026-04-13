import { Shield, CheckCircle2, XCircle, Settings } from 'lucide-react'
import Card from '../common/Card'
import type { PolicyAction } from '../../types'

interface PolicyActionsViewerProps {
  policyActions?: PolicyAction[]
  title?: string
  subtitle?: string
}

const formatActionLabel = (actionType: string) =>
  actionType
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')

const PolicyActionsViewer = ({
  policyActions = [],
  title = 'Policy Actions',
  subtitle = 'Vendor-neutral policy actions derived from gateway configuration',
}: PolicyActionsViewerProps) => {
  if (policyActions.length === 0) {
    return (
      <Card title={title} subtitle={subtitle}>
        <div className="flex items-center gap-3 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-sm text-gray-600">
          <Shield className="h-5 w-5 text-gray-400" />
          <span>No policy actions are currently defined for this API.</span>
        </div>
      </Card>
    )
  }

  return (
    <Card title={title} subtitle={subtitle}>
      <div className="space-y-3">
        {policyActions.map((policyAction, index) => (
          <div
            key={`${policyAction.action_type}-${policyAction.stage ?? 'none'}-${index}`}
            className="rounded-lg border border-gray-200 p-4"
          >
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
                    <Shield className="h-4 w-4" />
                    {policyAction.name || formatActionLabel(policyAction.action_type)}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${
                      policyAction.enabled
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {policyAction.enabled ? (
                      <CheckCircle2 className="h-3.5 w-3.5" />
                    ) : (
                      <XCircle className="h-3.5 w-3.5" />
                    )}
                    {policyAction.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                  {policyAction.stage && (
                    <span className="rounded-full bg-purple-50 px-2.5 py-1 text-xs font-medium text-purple-700">
                      Stage: {policyAction.stage}
                    </span>
                  )}
                </div>

                {policyAction.description && (
                  <p className="text-sm text-gray-600">{policyAction.description}</p>
                )}
              </div>

              {(policyAction.config && Object.keys(policyAction.config).length > 0) ||
              (policyAction.vendor_config &&
                Object.keys(policyAction.vendor_config).length > 0) ? (
                <div className="min-w-[240px] max-w-full rounded-lg bg-gray-50 p-3">
                  <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    <Settings className="h-4 w-4" />
                    Configuration
                  </div>

                  {policyAction.config && Object.keys(policyAction.config).length > 0 && (
                    <div className="mb-3">
                      <p className="mb-1 text-xs font-medium text-gray-500">Normalized</p>
                      <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-gray-800">
                        {JSON.stringify(policyAction.config, null, 2)}
                      </pre>
                    </div>
                  )}

                  {policyAction.vendor_config &&
                    Object.keys(policyAction.vendor_config).length > 0 && (
                      <div>
                        <p className="mb-1 text-xs font-medium text-gray-500">Vendor</p>
                        <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-gray-800">
                          {JSON.stringify(policyAction.vendor_config, null, 2)}
                        </pre>
                      </div>
                    )}
                </div>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

export default PolicyActionsViewer

// Made with Bob
