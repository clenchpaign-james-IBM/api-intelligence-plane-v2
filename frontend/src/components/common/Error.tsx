import { ReactNode } from 'react';
import Button from './Button';

/**
 * Error Component
 * 
 * Displays error messages with optional retry action.
 * Supports different error types and custom actions.
 */

export interface ErrorProps {
  title?: string;
  message: string;
  type?: 'error' | 'warning' | 'info';
  onRetry?: () => void;
  retryLabel?: string;
  children?: ReactNode;
  className?: string;
}

const Error = ({
  title = 'Error',
  message,
  type = 'error',
  onRetry,
  retryLabel = 'Try Again',
  children,
  className = '',
}: ErrorProps) => {
  // Type-specific styles
  const typeStyles = {
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      icon: 'text-red-600',
      title: 'text-red-900',
      message: 'text-red-700',
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      icon: 'text-yellow-600',
      title: 'text-yellow-900',
      message: 'text-yellow-700',
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      icon: 'text-blue-600',
      title: 'text-blue-900',
      message: 'text-blue-700',
    },
  };

  const styles = typeStyles[type];

  // Icon based on type
  const getIcon = () => {
    switch (type) {
      case 'error':
        return (
          <svg
            className={`h-6 w-6 ${styles.icon}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
      case 'warning':
        return (
          <svg
            className={`h-6 w-6 ${styles.icon}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        );
      case 'info':
        return (
          <svg
            className={`h-6 w-6 ${styles.icon}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
    }
  };

  return (
    <div className={`rounded-lg border ${styles.bg} ${styles.border} p-6 ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">{getIcon()}</div>
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${styles.title}`}>{title}</h3>
          <div className={`mt-2 text-sm ${styles.message}`}>
            <p>{message}</p>
          </div>
          {children && <div className="mt-4">{children}</div>}
          {onRetry && (
            <div className="mt-4">
              <Button onClick={onRetry} size="sm" variant="secondary">
                {retryLabel}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Error;

// Made with Bob
