import { Loading as CarbonLoading, InlineLoading } from '@carbon/react';

/**
 * Loading Component - Carbon Design System Wrapper
 * 
 * Wraps Carbon Loading components with custom props mapping.
 * Supports different sizes and full-screen overlay mode.
 */

export interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  fullScreen?: boolean;
  className?: string;
}

const Loading = ({
  size = 'md',
  message,
  fullScreen = false,
  className = '',
}: LoadingProps) => {
  // Map custom sizes to Carbon sizes
  const sizeMap = {
    sm: 'sm' as const,
    md: 'md' as const,
    lg: 'lg' as const,
  };

  if (fullScreen) {
    return (
      <div 
        style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(255, 255, 255, 0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <CarbonLoading withOverlay={false} />
          {message && (
            <p className="cds--type-body-01" style={{ marginTop: 'var(--cds-spacing-05)', color: 'var(--cds-text-secondary)' }}>
              {message}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div 
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--cds-spacing-07) 0',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        {message ? (
          <InlineLoading description={message} />
        ) : (
          <CarbonLoading small={size === 'sm'} withOverlay={false} />
        )}
      </div>
    </div>
  );
};

export default Loading;

// Made with Bob
