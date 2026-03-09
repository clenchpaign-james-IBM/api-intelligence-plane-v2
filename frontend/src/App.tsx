import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Page imports (will be created in user story implementation)
// import Dashboard from './pages/Dashboard';
// import APIs from './pages/APIs';
// import Metrics from './pages/Metrics';
// import Predictions from './pages/Predictions';
// import Security from './pages/Security';
// import Query from './pages/Query';

// Placeholder components for routes
const Dashboard = () => <div className="p-6"><h1 className="text-2xl font-bold">Dashboard</h1></div>;
const APIs = () => <div className="p-6"><h1 className="text-2xl font-bold">APIs</h1></div>;
const Metrics = () => <div className="p-6"><h1 className="text-2xl font-bold">Metrics</h1></div>;
const Predictions = () => <div className="p-6"><h1 className="text-2xl font-bold">Predictions</h1></div>;
const Security = () => <div className="p-6"><h1 className="text-2xl font-bold">Security</h1></div>;
const Query = () => <div className="p-6"><h1 className="text-2xl font-bold">Natural Language Query</h1></div>;
const NotFound = () => <div className="p-6"><h1 className="text-2xl font-bold">404 - Page Not Found</h1></div>;

// Create QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

/**
 * Main App component with routing configuration.
 * 
 * Routes:
 * - / : Dashboard (default)
 * - /apis : API Inventory
 * - /metrics : Performance Metrics
 * - /predictions : Failure Predictions
 * - /security : Security Findings
 * - /query : Natural Language Query Interface
 */
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          {/* Navigation will be added in user story implementation */}
          <nav className="bg-white shadow-sm border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex">
                  <div className="flex-shrink-0 flex items-center">
                    <h1 className="text-xl font-bold text-gray-900">
                      API Intelligence Plane
                    </h1>
                  </div>
                  <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                    <a
                      href="/"
                      className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                    >
                      Dashboard
                    </a>
                    <a
                      href="/apis"
                      className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                    >
                      APIs
                    </a>
                    <a
                      href="/metrics"
                      className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                    >
                      Metrics
                    </a>
                    <a
                      href="/predictions"
                      className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                    >
                      Predictions
                    </a>
                    <a
                      href="/security"
                      className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                    >
                      Security
                    </a>
                    <a
                      href="/query"
                      className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                    >
                      Query
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </nav>

          {/* Main content */}
          <main>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/apis" element={<APIs />} />
              <Route path="/metrics" element={<Metrics />} />
              <Route path="/predictions" element={<Predictions />} />
              <Route path="/security" element={<Security />} />
              <Route path="/query" element={<Query />} />
              <Route path="/404" element={<NotFound />} />
              <Route path="*" element={<Navigate to="/404" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>

      {/* React Query Devtools (only in development) */}
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}

export default App;

// Made with Bob
