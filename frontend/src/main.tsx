import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

/**
 * Application Entry Point
 * 
 * Initializes the React application with:
 * - Strict Mode for development checks
 * - TanStack Query configuration (handled in App.tsx)
 * - Global styles
 */

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Failed to find the root element');
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);

// Made with Bob
