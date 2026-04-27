import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { Activity, AlertTriangle, Server, Zap, Plus } from 'lucide-react';
import Card from '../components/common/Card';
import Loading from '../components/common/Loading';
import Error from '../components/common/Error';
import GatewaySelector from '../components/common/GatewaySelector';
import AddGatewayForm from '../components/gateways/AddGatewayForm';
import TimeRangeSelector, { type TimeRangeValue } from '../components/common/TimeRangeSelector';
import { api } from '../services/api';
import { metricsService } from '../services/metrics';
import { securityService } from '../services/security';
import { optimizationService } from '../services/optimization';
import type { DashboardStats, API, Gateway } from '../types';

/**
 * Dashboard Page
 *
 * Displays overview of the API Intelligence Plane system:
 * - Key metrics and statistics
 * - API health overview
 * - Gateway status
 * - Recent alerts and recommendations
 */
const Dashboard = () => {
  const { gatewayId } = useParams<{ gatewayId?: string }>();
  const [selectedGatewayId, setSelectedGatewayId] = useState<string | null>(gatewayId || null);
  const [showAddGatewayForm, setShowAddGatewayForm] = useState(false);
  const [timeRange, setTimeRange] = useState<TimeRangeValue>({
    range: '24h',
    start: new Date(Date.now() - 24 * 60 * 60 * 1000),
    end: new Date(),
  });

  // Handle gateway selection
  const handleGatewayChange = (newGatewayId: string | null) => {
    setSelectedGatewayId(newGatewayId);
    // Update URL if needed (optional - can navigate to gateway-specific route)
    // if (newGatewayId) {
    //   navigate(`/?gateway=${newGatewayId}`);
    // } else {
    //   navigate('/');
    // }
  };

  // Fetch dashboard data (filtered by gateway if selected)
  const { data: apis, isLoading: apisLoading, error: apisError } = useQuery({
    queryKey: ['apis', selectedGatewayId],
    queryFn: () => {
      const params: any = {};
      if (selectedGatewayId) params.gateway_id = selectedGatewayId;
      return api.apis.list(params);
    },
    staleTime: 0, // Always fetch fresh data
  });

  const { data: gateways, isLoading: gatewaysLoading, error: gatewaysError, refetch: refetchGateways } = useQuery({
    queryKey: ['gateways'],
    queryFn: () => api.gateways.list(),
    staleTime: 0, // Always fetch fresh data
  });

  // Fetch metrics summary (filtered by gateway if selected)
  const { data: metricsSummary, isLoading: metricsLoading } = useQuery({
    queryKey: ['metrics-summary', timeRange, selectedGatewayId],
    queryFn: () => {
      const params: any = {
        start_time: timeRange.start?.toISOString(),
        end_time: timeRange.end?.toISOString(),
      };
      if (selectedGatewayId) params.gateway_id = selectedGatewayId;
      return metricsService.getSummary(params);
    },
    staleTime: 0, // Always fetch fresh data
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch security summary (filtered by gateway if selected)
  const { data: securitySummary, isLoading: securityLoading } = useQuery({
    queryKey: ['security-summary', selectedGatewayId],
    queryFn: () => {
      const params: any = {};
      if (selectedGatewayId) params.gateway_id = selectedGatewayId;
      return securityService.getSummary(params);
    },
    staleTime: 0, // Always fetch fresh data
    refetchInterval: 60000, // Refresh every minute
  });

  // Fetch optimization summary (filtered by gateway if selected)
  const { data: optimizationSummary, isLoading: optimizationLoading } = useQuery({
    queryKey: ['optimization-summary', selectedGatewayId],
    queryFn: () => {
      const params: any = {};
      if (selectedGatewayId) params.gateway_id = selectedGatewayId;
      return optimizationService.getSummary(params);
    },
    staleTime: 0, // Always fetch fresh data
    refetchInterval: 60000, // Refresh every minute
  });

  // Calculate dashboard statistics
  const stats: DashboardStats = {
    total_apis: apis?.items?.length || 0,
    active_apis: apis?.items?.filter((a: API) => a.status === 'active').length || 0,
    shadow_apis: apis?.items?.filter((a: API) => a.intelligence_metadata?.is_shadow).length || 0,
    total_gateways: gateways?.items?.length || 0,
    active_gateways: gateways?.items?.filter((g: Gateway) => g.status === 'connected').length || 0,
    avg_health_score: apis?.items?.length
      ? apis.items.reduce((sum: number, a: API) => sum + (a.intelligence_metadata?.health_score ?? 0), 0) / apis.items.length
      : 0,
    avg_response_time: metricsSummary?.avg_response_time || 0,
    total_requests_24h: metricsSummary?.total_requests_24h || 0,
    error_rate_24h: metricsSummary?.avg_error_rate || 0,
    critical_vulnerabilities: securitySummary?.critical_vulnerabilities || 0,
    high_priority_recommendations: optimizationSummary?.high_priority_recommendations || 0,
  };

  // Loading state
  if (apisLoading || gatewaysLoading || metricsLoading || securityLoading || optimizationLoading) {
    return (
      <div className="p-6">
        <Loading message="Loading dashboard..." />
      </div>
    );
  }

  // Error state
  if (apisError || gatewaysError) {
    return (
      <div className="p-6">
        <Error
          message="Failed to load dashboard data"
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-600">
          Overview of your API infrastructure and health metrics
        </p>
      </div>

      {/* Gateway and Time Range Selectors */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GatewaySelector
          selectedGatewayId={selectedGatewayId}
          onGatewayChange={handleGatewayChange}
          showAllOption={true}
        />
        <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total APIs */}
        <Link to="/apis" className="block">
          <Card padding="md" className="hover:shadow-lg transition-shadow cursor-pointer">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total APIs</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">{stats.total_apis}</p>
                <p className="mt-1 text-sm text-gray-500">
                  {stats.active_apis} active
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <Server className="w-8 h-8 text-blue-600" />
              </div>
            </div>
          </Card>
        </Link>

        {/* Average Health Score */}
        <Link to="/apis?health=low" className="block">
          <Card padding="md" className="hover:shadow-lg transition-shadow cursor-pointer">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Health Score</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">
                  {stats.avg_health_score.toFixed(1)}
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  out of 100
                </p>
              </div>
              <div className={`p-3 rounded-lg ${
                stats.avg_health_score >= 80 ? 'bg-green-100' :
                stats.avg_health_score >= 50 ? 'bg-yellow-100' : 'bg-red-100'
              }`}>
                <Activity className={`w-8 h-8 ${
                  stats.avg_health_score >= 80 ? 'text-green-600' :
                  stats.avg_health_score >= 50 ? 'text-yellow-600' : 'text-red-600'
                }`} />
              </div>
            </div>
          </Card>
        </Link>

        {/* Shadow APIs */}
        <Link to="/apis?shadow=true" className="block">
          <Card padding="md" className="hover:shadow-lg transition-shadow cursor-pointer">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Shadow APIs</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">{stats.shadow_apis}</p>
                <p className="mt-1 text-sm text-gray-500">
                  {stats.shadow_apis > 0 ? 'Needs attention' : 'All documented'}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${
                stats.shadow_apis > 0 ? 'bg-orange-100' : 'bg-green-100'
              }`}>
                <AlertTriangle className={`w-8 h-8 ${
                  stats.shadow_apis > 0 ? 'text-orange-600' : 'text-green-600'
                }`} />
              </div>
            </div>
          </Card>
        </Link>

        {/* Active Gateways */}
        <Link to="/gateways" className="block">
          <Card padding="md" className="hover:shadow-lg transition-shadow cursor-pointer">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Gateways</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">{stats.active_gateways}</p>
                <p className="mt-1 text-sm text-gray-500">
                  of {stats.total_gateways} total
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-lg">
                <Zap className="w-8 h-8 text-purple-600" />
              </div>
            </div>
          </Card>
        </Link>
      </div>

      {/* API Health Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top APIs by Health Score */}
        <Card title="Top Performing APIs" subtitle="Highest health scores">
          <div className="space-y-3">
            {apis?.items
              ?.sort((a: API, b: API) => (b.intelligence_metadata?.health_score ?? 0) - (a.intelligence_metadata?.health_score ?? 0))
              .slice(0, 5)
              .map((api: API) => (
                <Link
                  key={api.id}
                  to={`/apis/detail/${api.id}`}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                >
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{api.name}</p>
                    <p className="text-sm text-gray-500">{api.base_path}</p>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {(api.intelligence_metadata?.health_score ?? 0).toFixed(1)}
                      </p>
                      <p className="text-xs text-gray-500">Health Score</p>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${
                      (api.intelligence_metadata?.health_score ?? 0) >= 80 ? 'bg-green-500' :
                      (api.intelligence_metadata?.health_score ?? 0) >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
                  </div>
                </Link>
              ))}
            {(!apis?.items || apis.items.length === 0) && (
              <p className="text-center text-gray-500 py-4">No APIs found</p>
            )}
          </div>
        </Card>

        {/* APIs Needing Attention */}
        <Card title="APIs Needing Attention" subtitle="Low health scores or issues">
          <div className="space-y-3">
            {apis?.items
              ?.filter((a: API) => (a.intelligence_metadata?.health_score ?? 0) < 70 || a.status === 'failed')
              .sort((a: API, b: API) => (a.intelligence_metadata?.health_score ?? 0) - (b.intelligence_metadata?.health_score ?? 0))
              .slice(0, 5)
              .map((api: API) => (
                <Link
                  key={api.id}
                  to={`/apis/detail/${api.id}`}
                  className="flex items-center justify-between p-3 bg-red-50 rounded-lg hover:bg-red-100 transition-colors cursor-pointer"
                >
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{api.name}</p>
                    <p className="text-sm text-gray-500">{api.base_path}</p>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <p className="text-sm font-medium text-red-600">
                        {(api.intelligence_metadata?.health_score ?? 0).toFixed(1)}
                      </p>
                      <p className="text-xs text-gray-500">Health Score</p>
                    </div>
                    <AlertTriangle className="w-5 h-5 text-red-500" />
                  </div>
                </Link>
              ))}
            {(!apis?.items || apis.items.filter((a: API) => (a.intelligence_metadata?.health_score ?? 0) < 70).length === 0) && (
              <p className="text-center text-green-600 py-4">
                All APIs are performing well! 🎉
              </p>
            )}
          </div>
        </Card>
      </div>

      {/* Gateway Status */}
      <Card title="Gateway Status" subtitle="Connected API gateways">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {gateways?.items?.map((gateway: Gateway) => (
            <Link
              key={gateway.id}
              to={`/gateways/${gateway.id}`}
              className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{gateway.name}</h4>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  gateway.status === 'connected' ? 'bg-green-100 text-green-800' :
                  gateway.status === 'disconnected' ? 'bg-gray-100 text-gray-800' :
                  gateway.status === 'maintenance' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {gateway.status}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{gateway.vendor}</p>
              <p className="text-xs text-gray-500 truncate">{gateway.base_url}</p>
              {gateway.last_connected_at && (
                <p className="text-xs text-gray-400 mt-2">
                  Last connected: {new Date(gateway.last_connected_at).toLocaleString()}
                </p>
              )}
            </Link>
          ))}
          {(!gateways?.items || gateways.items.length === 0) && (
            <div className="col-span-full text-center text-gray-500 py-8">
              No gateways configured. Add a gateway to start discovering APIs.
            </div>
          )}
        </div>
      </Card>

      {/* Quick Actions */}
      <Card title="Quick Actions" padding="md">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => setShowAddGatewayForm(true)}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors text-center"
          >
            <Plus className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="font-medium text-gray-900">Add Gateway</p>
            <p className="text-sm text-gray-500 mt-1">Connect a new API gateway</p>
          </button>
          <Link
            to="/apis"
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-center block"
          >
            <Server className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="font-medium text-gray-900">View All APIs</p>
            <p className="text-sm text-gray-500 mt-1">Browse API inventory</p>
          </Link>
          <Link
            to="/metrics"
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-center block"
          >
            <Activity className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="font-medium text-gray-900">View Metrics</p>
            <p className="text-sm text-gray-500 mt-1">Analyze performance</p>
          </Link>
        </div>
      </Card>

      {/* Add Gateway Modal */}
      {showAddGatewayForm && (
        <AddGatewayForm
          onClose={() => setShowAddGatewayForm(false)}
          onSuccess={() => {
            setShowAddGatewayForm(false);
            refetchGateways();
          }}
        />
      )}
    </div>
  );
};

export default Dashboard;

// Made with Bob