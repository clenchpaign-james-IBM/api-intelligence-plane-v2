/**
 * Confirmation Modal Component
 * 
 * A reusable modal for confirming actions with optional progress indicator
 */

import React from 'react';

interface ConfirmationModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  isProcessing?: boolean;
  processingMessage?: string;
  successMessage?: string;
  errorMessage?: string;
  showProgress?: boolean;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  isProcessing = false,
  processingMessage = 'Processing...',
  successMessage,
  errorMessage,
}) => {
  if (!isOpen) return null;

  const hasCompleted = !isProcessing && (successMessage || errorMessage);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={!isProcessing ? onCancel : undefined}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          {/* Header */}
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          </div>

          {/* Content */}
          <div className="mb-6">
            {!isProcessing && !hasCompleted && (
              <p className="text-sm text-gray-600">{message}</p>
            )}

            {isProcessing && (
              <div className="flex flex-col items-center justify-center py-4">
                {/* Circular Progress Indicator */}
                <div className="relative w-16 h-16 mb-4">
                  <svg className="w-16 h-16 transform -rotate-90">
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                      className="text-gray-200"
                    />
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                      strokeDasharray="175.93"
                      strokeDashoffset="0"
                      className="text-blue-600 animate-spin-slow"
                      style={{
                        animation: 'spin 2s linear infinite',
                      }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg
                      className="w-8 h-8 text-blue-600 animate-pulse"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 10V3L4 14h7v7l9-11h-7z"
                      />
                    </svg>
                  </div>
                </div>
                <p className="text-sm text-gray-600 text-center">{processingMessage}</p>
              </div>
            )}

            {successMessage && (
              <div className="flex flex-col items-center justify-center py-4">
                <div className="w-16 h-16 mb-4 rounded-full bg-green-100 flex items-center justify-center">
                  <svg
                    className="w-8 h-8 text-green-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
                <p className="text-sm text-green-600 text-center font-medium">{successMessage}</p>
              </div>
            )}

            {errorMessage && (
              <div className="flex flex-col items-center justify-center py-4">
                <div className="w-16 h-16 mb-4 rounded-full bg-red-100 flex items-center justify-center">
                  <svg
                    className="w-8 h-8 text-red-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </div>
                <p className="text-sm text-red-600 text-center font-medium">{errorMessage}</p>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            {!isProcessing && !hasCompleted && (
              <>
                <button
                  onClick={onCancel}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {cancelLabel}
                </button>
                <button
                  onClick={onConfirm}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  {confirmLabel}
                </button>
              </>
            )}

            {hasCompleted && (
              <button
                onClick={onCancel}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Close
              </button>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from {
            stroke-dashoffset: 175.93;
          }
          to {
            stroke-dashoffset: 0;
          }
        }
      `}</style>
    </div>
  );
};

// Made with Bob