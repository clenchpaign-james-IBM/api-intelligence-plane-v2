import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  Header,
  HeaderContainer,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderGlobalBar,
  HeaderGlobalAction,
  SkipToContent,
  Content,
  Theme,
} from '@carbon/react';
import { Notification, UserAvatar } from '@carbon/icons-react';

// Page imports
import Dashboard from './pages/Dashboard';
import APIs from './pages/APIs';
import Gateways from './pages/Gateways';
import Predictions from './pages/Predictions';
import Optimization from './pages/Optimization';
import { Query } from './pages/Query';

// Placeholder components for routes
const Metrics = () => (
  <div style={{ padding: '2rem' }}>
    <h1>Metrics</h1>
    <p>Performance metrics will be displayed here.</p>
  </div>
);

const Security = () => (
  <div style={{ padding: '2rem' }}>
    <h1>Security</h1>
    <p>Security findings will be displayed here.</p>
  </div>
);

const NotFound = () => (
  <div style={{ padding: '2rem' }}>
    <h1>404 - Page Not Found</h1>
    <p>The page you are looking for does not exist.</p>
  </div>
);

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
 * Navigation component with Carbon UI Shell
 */
function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <HeaderContainer
      render={({ isSideNavExpanded, onClickSideNavExpand }) => (
        <Header aria-label="API Intelligence Plane">
          <SkipToContent />
          <HeaderName href="/" prefix="" style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
            API Intelligence Plane
          </HeaderName>
          <HeaderNavigation aria-label="API Intelligence Plane">
            <HeaderMenuItem
              href="/"
              isActive={isActive('/')}
              onClick={(e) => {
                e.preventDefault();
                navigate('/');
              }}
            >
              Dashboard
            </HeaderMenuItem>
            <HeaderMenuItem
              href="/apis"
              isActive={isActive('/apis')}
              onClick={(e) => {
                e.preventDefault();
                navigate('/apis');
              }}
            >
              APIs
            </HeaderMenuItem>
            <HeaderMenuItem
              href="/gateways"
              isActive={isActive('/gateways')}
              onClick={(e) => {
                e.preventDefault();
                navigate('/gateways');
              }}
            >
              Gateways
            </HeaderMenuItem>
            <HeaderMenuItem
              href="/predictions"
              isActive={isActive('/predictions')}
              onClick={(e) => {
                e.preventDefault();
                navigate('/predictions');
              }}
            >
              Predictions
            </HeaderMenuItem>
            <HeaderMenuItem
              href="/optimization"
              isActive={isActive('/optimization')}
              onClick={(e) => {
                e.preventDefault();
                navigate('/optimization');
              }}
            >
              Optimization
            </HeaderMenuItem>
            <HeaderMenuItem
              href="/query"
              isActive={isActive('/query')}
              onClick={(e) => {
                e.preventDefault();
                navigate('/query');
              }}
            >
              Query
            </HeaderMenuItem>
          </HeaderNavigation>
          <HeaderGlobalBar>
            <HeaderGlobalAction
              aria-label="Notifications"
              tooltipAlignment="end"
            >
              <Notification size={20} />
            </HeaderGlobalAction>
            <HeaderGlobalAction
              aria-label="User Avatar"
              tooltipAlignment="end"
            >
              <UserAvatar size={20} />
            </HeaderGlobalAction>
          </HeaderGlobalBar>
        </Header>
      )}
    />
  );
}

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
        <Theme theme="g10">
          <Navigation />
          <Content>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/apis" element={<APIs />} />
              <Route path="/gateways" element={<Gateways />} />
              <Route path="/metrics" element={<Metrics />} />
              <Route path="/predictions" element={<Predictions />} />
              <Route path="/optimization" element={<Optimization />} />
              <Route path="/security" element={<Security />} />
              <Route path="/query" element={<Query />} />
              <Route path="/404" element={<NotFound />} />
              <Route path="*" element={<Navigate to="/404" replace />} />
            </Routes>
          </Content>
        </Theme>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

// Made with Bob
