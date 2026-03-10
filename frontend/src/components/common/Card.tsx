import { ReactNode } from 'react';

/**
 * Card Component
 * 
 * Reusable card container with optional header and footer.
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
  // Padding styles
  const paddingStyles = {
    none: '',
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      {(title || subtitle) && (
        <div className={`border-b border-gray-200 ${paddingStyles[padding]}`}>
          {title && (
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          )}
          {subtitle && (
            <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
          )}
        </div>
      )}

      {/* Content */}
      <div className={paddingStyles[padding]}>
        {children}
      </div>

      {/* Footer */}
      {footer && (
        <div className={`border-t border-gray-200 ${paddingStyles[padding]} bg-gray-50`}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;

// Made with Bob
