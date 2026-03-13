import { Button as CarbonButton } from '@carbon/react';
import { ReactNode } from 'react';
import type { ButtonProps as CarbonButtonProps } from '@carbon/react';

/**
 * Button Component - Carbon Design System Wrapper
 *
 * Wraps Carbon Button component with custom props mapping.
 * Maintains API compatibility with previous implementation.
 */

export interface ButtonProps extends Omit<CarbonButtonProps<'button'>, 'kind' | 'size'> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: ReactNode;
}

const Button = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) => {
  // Map custom variants to Carbon kinds
  const kindMap: Record<string, CarbonButtonProps<'button'>['kind']> = {
    primary: 'primary',
    secondary: 'secondary',
    danger: 'danger',
    ghost: 'ghost',
  };

  // Map custom sizes to Carbon sizes
  const sizeMap: Record<string, CarbonButtonProps<'button'>['size']> = {
    sm: 'sm',
    md: 'md',
    lg: 'lg',
  };

  return (
    <CarbonButton
      kind={kindMap[variant]}
      size={sizeMap[size]}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </CarbonButton>
  );
};

export default Button;

// Made with Bob
