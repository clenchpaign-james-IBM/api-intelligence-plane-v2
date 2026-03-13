import { ReactNode } from 'react';
import { Tile } from '@carbon/react';

/**
 * Card Component - Carbon Design System Wrapper
 * 
 * Wraps Carbon Tile component with custom header and footer support.
 * Provides consistent styling for content sections.
 */

export interface CardProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const Card = ({
  title,
  subtitle,
  children,
  footer,
  className = '',
  padding = 'md',
}: CardProps) => {
  // Padding styles using Carbon spacing tokens
  const paddingStyles = {
    none: '',
    sm: 'cds--spacing-03',
    md: 'cds--spacing-05',
    lg: 'cds--spacing-07',
  };

  const paddingClass = paddingStyles[padding];

  return (
    <Tile className={className}>
      {/* Header */}
      {(title || subtitle) && (
        <div className={`${paddingClass}`} style={{ borderBottom: '1px solid var(--cds-border-subtle-01)', marginBottom: 'var(--cds-spacing-05)' }}>
          {title && (
            <h3 className="cds--type-heading-03" style={{ marginBottom: subtitle ? 'var(--cds-spacing-02)' : 0 }}>
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="cds--type-body-01" style={{ color: 'var(--cds-text-secondary)' }}>
              {subtitle}
            </p>
          )}
        </div>
      )}

      {/* Content */}
      <div className={paddingClass}>
        {children}
      </div>

      {/* Footer */}
      {footer && (
        <div 
          className={paddingClass} 
          style={{ 
            borderTop: '1px solid var(--cds-border-subtle-01)', 
            marginTop: 'var(--cds-spacing-05)',
            backgroundColor: 'var(--cds-layer-01)'
          }}
        >
          {footer}
        </div>
      )}
    </Tile>
  );
};

export default Card;

// Made with Bob
