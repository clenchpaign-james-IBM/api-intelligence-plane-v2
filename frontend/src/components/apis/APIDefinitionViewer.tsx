import { useState } from 'react';
import { Code, ChevronDown, ChevronRight, FileJson } from 'lucide-react';
import Card from '../common/Card';
import type { APIDefinition } from '../../types';

/**
 * API Definition Viewer Component
 * 
 * Displays OpenAPI/Swagger definition with:
 * - Syntax highlighting for JSON
 * - Collapsible sections for paths, schemas, security
 * - Copy to clipboard functionality
 * - Formatted display
 */

interface APIDefinitionViewerProps {
  apiDefinition?: APIDefinition;
  title?: string;
  subtitle?: string;
}

interface CollapsibleSectionProps {
  title: string;
  content: any;
  defaultOpen?: boolean;
}

const CollapsibleSection = ({ title, content, defaultOpen = false }: CollapsibleSectionProps) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (!content || (typeof content === 'object' && Object.keys(content).length === 0)) {
    return null;
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <span className="font-medium text-gray-900">{title}</span>
        {isOpen ? (
          <ChevronDown className="w-5 h-5 text-gray-600" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-600" />
        )}
      </button>
      {isOpen && (
        <div className="p-4 bg-white">
          <pre className="text-sm text-gray-800 overflow-x-auto">
            <code>{JSON.stringify(content, null, 2)}</code>
          </pre>
        </div>
      )}
    </div>
  );
};

const APIDefinitionViewer = ({
  apiDefinition,
  title = 'API Definition',
  subtitle = 'OpenAPI/Swagger specification',
}: APIDefinitionViewerProps) => {
  const [copied, setCopied] = useState(false);

  if (!apiDefinition) {
    return (
      <Card title={title} subtitle={subtitle}>
        <div className="flex items-center gap-3 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-sm text-gray-600">
          <FileJson className="h-5 w-5 text-gray-400" />
          <span>No API definition available for this API.</span>
        </div>
      </Card>
    );
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(apiDefinition, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <Card title={title} subtitle={subtitle}>
      <div className="space-y-4">
        {/* Header with metadata */}
        <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center gap-3">
            <Code className="w-5 h-5 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-blue-900">
                {apiDefinition.type || 'OpenAPI'} {apiDefinition.version || apiDefinition.swagger_version || ''}
              </p>
              <p className="text-xs text-blue-700">
                Base Path: {apiDefinition.base_path}
              </p>
            </div>
          </div>
          <button
            onClick={handleCopy}
            className="px-3 py-1.5 text-sm font-medium text-blue-700 bg-white border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
          >
            {copied ? 'Copied!' : 'Copy JSON'}
          </button>
        </div>

        {/* Collapsible sections */}
        <div className="space-y-3">
          {/* Full OpenAPI Spec */}
          {apiDefinition.openapi_spec && (
            <CollapsibleSection
              title="Complete OpenAPI Specification"
              content={apiDefinition.openapi_spec}
              defaultOpen={true}
            />
          )}

          {/* Paths */}
          {apiDefinition.paths && (
            <CollapsibleSection
              title={`Paths (${Object.keys(apiDefinition.paths).length})`}
              content={apiDefinition.paths}
            />
          )}

          {/* Schemas */}
          {apiDefinition.schemas && (
            <CollapsibleSection
              title={`Schemas (${Object.keys(apiDefinition.schemas).length})`}
              content={apiDefinition.schemas}
            />
          )}

          {/* Security Schemes */}
          {apiDefinition.security_schemes && (
            <CollapsibleSection
              title={`Security Schemes (${Object.keys(apiDefinition.security_schemes).length})`}
              content={apiDefinition.security_schemes}
            />
          )}

          {/* Vendor Extensions */}
          {apiDefinition.vendor_extensions && Object.keys(apiDefinition.vendor_extensions).length > 0 && (
            <CollapsibleSection
              title="Vendor Extensions"
              content={apiDefinition.vendor_extensions}
            />
          )}
        </div>

        {/* Info message if no detailed sections */}
        {!apiDefinition.openapi_spec && 
         !apiDefinition.paths && 
         !apiDefinition.schemas && 
         !apiDefinition.security_schemes && (
          <div className="p-4 bg-gray-50 rounded-lg text-sm text-gray-600">
            <p>API definition structure is available but detailed specification sections are not populated.</p>
            <p className="mt-2">Type: {apiDefinition.type || 'Unknown'}</p>
            {apiDefinition.version && <p>Version: {apiDefinition.version}</p>}
            {apiDefinition.swagger_version && <p>Swagger Version: {apiDefinition.swagger_version}</p>}
          </div>
        )}
      </div>
    </Card>
  );
};

export default APIDefinitionViewer;

// Made with Bob
