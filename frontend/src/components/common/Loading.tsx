/**
 * Loading Component
 * 
 * Displays loading states with spinner and optional message.
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
  // Size styles for spinner
  const sizeStyles = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2',
    lg: 'h-12 w-12 border-3',
  };

  const spinner = (
    <div className="flex flex-col items-center justify-center">
      <div
        className={`animate-spin rounded-full border-blue-600 border-t-transparent ${sizeStyles[size]}`}
      />
      {message && (
        <p className="mt-4 text-sm text-gray-600">{message}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        {spinner}
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-center py-8 ${className}`}>
      {spinner}
    </div>
  );
};

export default Loading;

// Made with Bob
