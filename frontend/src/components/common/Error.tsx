import { ReactNode } from 'react';
import { InlineNotification } from '@carbon/react';
import Button from './Button';

/**
 * Error Component - Carbon Design System Wrapper
 * 
 * Wraps Carbon InlineNotification with custom retry action support.
 * Supports different notification types and custom actions.
 */

export interface ErrorProps {
  title?: string;
  message: string;
  type?: 'error' | 'warning' | 'info';
  onRetry?: () => void;
  retryLabel?: string;
  children?: ReactNode;
  className?: string;
  details?: Error;
}

const Error = ({
  title = 'Error',
  message,
  type = 'error',
  onRetry,
  retryLabel = 'Try Again',
  children,
  className = '',
  details,
}: ErrorProps) => {
  // Map custom types to Carbon kinds
  const kindMap = {
    error: 'error' as const,
    warning: 'warning' as const,
    info: 'info' as const,
  };

  // Format error details if provided
  const subtitle = details 
    ? `${message}\n\nDetails: ${details.message}`
    : message;

  return (
    <div className={className}>
      <InlineNotification
        kind={kindMap[type]}
        title={title}
        subtitle={subtitle}
        hideCloseButton={false}
        lowContrast
      />
      
      {children && (
        <div style={{ marginTop: 'var(--cds-spacing-05)' }}>
          {children}
        </div>
      )}
      
      {onRetry && (
        <div style={{ marginTop: 'var(--cds-spacing-05)' }}>
          <Button onClick={onRetry} size="sm" variant="secondary">
            {retryLabel}
          </Button>
        </div>
      )}
    </div>
  );
};

export default Error;

// Made with Bob
