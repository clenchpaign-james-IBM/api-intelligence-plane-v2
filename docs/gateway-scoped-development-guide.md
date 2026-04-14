# Gateway-Scoped Development Guide

**API Intelligence Plane v2 - Developer Guide**  
**Version**: 2.0.0  
**Last Updated**: 2026-04-14  
**Architecture**: Gateway-First, API-Secondary

---

## Table of Contents

1. [Overview](#overview)
2. [Scope Dimension Architecture](#scope-dimension-architecture)
3. [Data Model Guidelines](#data-model-guidelines)
4. [Backend Development](#backend-development)
5. [Frontend Development](#frontend-development)
6. [Testing Guidelines](#testing-guidelines)
7. [Common Patterns](#common-patterns)
8. [Migration Checklist](#migration-checklist)

---

## 1. Overview

This guide provides comprehensive instructions for developing features in the API Intelligence Plane with the **Gateway-First, API-Secondary** architecture. All features must follow this scope dimension hierarchy to ensure consistency and proper multi-gateway support.

### Key Principles

- **Gateway is Primary**: All data operations start with gateway context
- **API is Secondary**: APIs exist within gateway context
- **No Cross-Gateway Defaults**: Never aggregate across gateways by default
- **Explicit Gateway Selection**: Users must explicitly select gateway for cross-gateway views

### Scope Hierarchy

```
Gateway (Primary Dimension)
  └── API (Secondary Dimension)
      └── Endpoint (Tertiary Dimension)
          └── Operation (Quaternary Dimension)
```

---

## 2. Scope Dimension Architecture

### 2.1 Correct vs Incorrect Scoping

#### ✅ CORRECT: Gateway-First

```python
# Backend: Gateway-scoped query
async def get_metrics(
    gateway_id: UUID,              # REQUIRED primary filter
    api_id: Optional[UUID] = None, # Optional secondary filter
    time_range: TimeRange = None
) -> List[Metric]:
    query = {"gateway_id": str(gateway_id)}
    if api_id:
        query["api_id"] = str(api_id)
    return await metrics_repo.find(query)
```

```typescript
// Frontend: Gateway-scoped component
function MetricsDashboard() {
  const [selectedGateway, setSelectedGateway] = useState<string | null>(null);
  const [selectedApi, setSelectedApi] = useState<string | null>(null);
  
  // Gateway filter is primary and required
  const { data: metrics } = useMetrics({
    gatewayId: selectedGateway,  // Required
    apiId: selectedApi,          // Optional
  });
  
  return (
    <>
      <GatewaySelector 
        value={selectedGateway}
        onChange={setSelectedGateway}
        required
      />
      {selectedGateway && (
        <ApiSelector 
          gatewayId={selectedGateway}
          value={selectedApi}
          onChange={setSelectedApi}
        />
      )}
    </>
  );
}
```

#### ❌ INCORRECT: API-First

```python
# WRONG: API-scoped query without gateway context
async def get_metrics(
    api_id: UUID,                      # WRONG: API as primary
    gateway_id: Optional[UUID] = None  # WRONG: Gateway as optional
) -> List[Metric]:
    query = {"api_id": str(api_id)}
    if gateway_id:
        query["gateway_id"] = str(gateway_id)
    return await metrics_repo.find(query)
```

```typescript
// WRONG: API-scoped component
function MetricsDashboard() {
  const [selectedApi, setSelectedApi] = useState<string | null>(null);
  
  // WRONG: No gateway context
  const { data: metrics } = useMetrics({
    apiId: selectedApi,
  });
  
  return <ApiSelector value={selectedApi} onChange={setSelectedApi} />;
}
```

### 2.2 Multi-Gateway Scenarios

#### Scenario 1: Single Gateway View (Default)

```python
# User selects one gateway
gateway_id = "gateway-123"
apis = await api_repo.find_by_gateway(gateway_id)
metrics = await metrics_repo.find({"gateway_id": str(gateway_id)})
```

#### Scenario 2: Cross-Gateway View (Explicit)

```python
# User explicitly selects "All Gateways"
if gateway_id is None:  # Explicit "All Gateways" selection
    apis = await api_repo.find_all()
    metrics = await metrics_repo.find({})
else:
    apis = await api_repo.find_by_gateway(gateway_id)
    metrics = await metrics_repo.find({"gateway_id": str(gateway_id)})
```

#### Scenario 3: Multi-Gateway Comparison

```python
# User selects multiple gateways for comparison
gateway_ids = ["gateway-1", "gateway-2", "gateway-3"]
results = []
for gateway_id in gateway_ids:
    metrics = await metrics_repo.find({"gateway_id": str(gateway_id)})
    results.append({
        "gateway_id": gateway_id,
        "metrics": metrics
    })
```

---

## 3. Data Model Guidelines

### 3.1 Required Fields

All data models MUST include `gateway_id` as a required field:

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class Metric(BaseModel):
    """Vendor-neutral metric model."""
    
    # PRIMARY DIMENSION - REQUIRED
    gateway_id: UUID = Field(..., description="Gateway ID (primary dimension)")
    
    # SECONDARY DIMENSION - REQUIRED
    api_id: UUID = Field(..., description="API ID (secondary dimension)")
    
    # Timestamp
    timestamp: datetime = Field(..., description="Metric timestamp")
    
    # Metric data
    request_count: int = Field(default=0)
    error_count: int = Field(default=0)
    avg_response_time: float = Field(default=0.0)
    
    # Vendor-specific fields
    vendor_metadata: dict = Field(default_factory=dict)
```

### 3.2 Index Mappings

OpenSearch indices MUST include `gateway_id` in mappings:

```python
METRIC_MAPPING = {
    "properties": {
        "gateway_id": {"type": "keyword"},  # PRIMARY dimension
        "api_id": {"type": "keyword"},      # SECONDARY dimension
        "timestamp": {"type": "date"},
        "request_count": {"type": "long"},
        "error_count": {"type": "long"},
        "avg_response_time": {"type": "float"},
        "vendor_metadata": {"type": "object", "enabled": False}
    }
}
```

### 3.3 Repository Patterns

All repositories MUST support gateway-scoped queries:

```python
class MetricsRepository(BaseRepository):
    """Gateway-scoped metrics repository."""
    
    async def find_by_gateway(
        self,
        gateway_id: UUID,
        time_range: Optional[TimeRange] = None
    ) -> List[Metric]:
        """Find metrics for a specific gateway."""
        query = {"gateway_id": str(gateway_id)}
        
        if time_range:
            query["timestamp"] = {
                "gte": time_range.start.isoformat(),
                "lte": time_range.end.isoformat()
            }
        
        return await self.find(query)
    
    async def find_by_gateway_and_api(
        self,
        gateway_id: UUID,
        api_id: UUID,
        time_range: Optional[TimeRange] = None
    ) -> List[Metric]:
        """Find metrics for a specific API within a gateway."""
        query = {
            "gateway_id": str(gateway_id),
            "api_id": str(api_id)
        }
        
        if time_range:
            query["timestamp"] = {
                "gte": time_range.start.isoformat(),
                "lte": time_range.end.isoformat()
            }
        
        return await self.find(query)
```

---

## 4. Backend Development

### 4.1 API Endpoint Design

#### Pattern 1: Gateway-Scoped Endpoints

```python
from fastapi import APIRouter, Depends, Query
from typing import Optional
from uuid import UUID

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

@router.get("/")
async def get_metrics(
    gateway_id: UUID = Query(..., description="Gateway ID (required)"),
    api_id: Optional[UUID] = Query(None, description="API ID (optional)"),
    time_range: Optional[str] = Query("24h", description="Time range"),
    metrics_service: MetricsService = Depends(get_metrics_service)
) -> List[MetricResponse]:
    """
    Get metrics for a gateway.
    
    - **gateway_id**: Required gateway filter (primary dimension)
    - **api_id**: Optional API filter (secondary dimension)
    - **time_range**: Time range for metrics (default: 24h)
    """
    return await metrics_service.get_metrics(
        gateway_id=gateway_id,
        api_id=api_id,
        time_range=parse_time_range(time_range)
    )
```

#### Pattern 2: Cross-Gateway Endpoints (Explicit)

```python
@router.get("/cross-gateway")
async def get_cross_gateway_metrics(
    gateway_ids: List[UUID] = Query(..., description="Gateway IDs for comparison"),
    time_range: Optional[str] = Query("24h", description="Time range"),
    metrics_service: MetricsService = Depends(get_metrics_service)
) -> Dict[str, List[MetricResponse]]:
    """
    Get metrics across multiple gateways for comparison.
    
    - **gateway_ids**: List of gateway IDs (explicit multi-gateway)
    - **time_range**: Time range for metrics
    """
    results = {}
    for gateway_id in gateway_ids:
        metrics = await metrics_service.get_metrics(
            gateway_id=gateway_id,
            time_range=parse_time_range(time_range)
        )
        results[str(gateway_id)] = metrics
    return results
```

### 4.2 Service Layer Patterns

```python
class MetricsService:
    """Gateway-scoped metrics service."""
    
    def __init__(self, metrics_repo: MetricsRepository):
        self.metrics_repo = metrics_repo
    
    async def get_metrics(
        self,
        gateway_id: UUID,
        api_id: Optional[UUID] = None,
        time_range: Optional[TimeRange] = None
    ) -> List[Metric]:
        """
        Get metrics with gateway-first scoping.
        
        Args:
            gateway_id: Gateway ID (required primary dimension)
            api_id: API ID (optional secondary dimension)
            time_range: Time range for metrics
        
        Returns:
            List of metrics scoped to gateway (and optionally API)
        """
        if api_id:
            return await self.metrics_repo.find_by_gateway_and_api(
                gateway_id=gateway_id,
                api_id=api_id,
                time_range=time_range
            )
        else:
            return await self.metrics_repo.find_by_gateway(
                gateway_id=gateway_id,
                time_range=time_range
            )
    
    async def get_gateway_summary(
        self,
        gateway_id: UUID,
        time_range: Optional[TimeRange] = None
    ) -> GatewaySummary:
        """Get summary statistics for a gateway."""
        metrics = await self.get_metrics(gateway_id, time_range=time_range)
        
        return GatewaySummary(
            gateway_id=gateway_id,
            total_requests=sum(m.request_count for m in metrics),
            total_errors=sum(m.error_count for m in metrics),
            avg_response_time=sum(m.avg_response_time for m in metrics) / len(metrics) if metrics else 0,
            api_count=len(set(m.api_id for m in metrics))
        )
```

### 4.3 Background Jobs

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class MetricsCollectionJob:
    """Gateway-scoped metrics collection job."""
    
    async def collect_metrics_for_gateway(self, gateway_id: UUID):
        """Collect metrics for a specific gateway."""
        gateway = await gateway_repo.find_by_id(gateway_id)
        adapter = gateway_adapter_factory.get_adapter(gateway.vendor)
        
        # Collect metrics from gateway
        raw_metrics = await adapter.collect_metrics(gateway)
        
        # Transform to vendor-neutral format
        metrics = [
            Metric(
                gateway_id=gateway_id,
                api_id=m.api_id,
                timestamp=m.timestamp,
                request_count=m.request_count,
                error_count=m.error_count,
                avg_response_time=m.avg_response_time,
                vendor_metadata=m.vendor_specific_fields
            )
            for m in raw_metrics
        ]
        
        # Store metrics
        await metrics_repo.bulk_create(metrics)
    
    async def collect_all_gateways(self):
        """Collect metrics for all registered gateways."""
        gateways = await gateway_repo.find_all()
        
        for gateway in gateways:
            try:
                await self.collect_metrics_for_gateway(gateway.id)
            except Exception as e:
                logger.error(f"Failed to collect metrics for gateway {gateway.id}: {e}")
```

---

## 5. Frontend Development

### 5.1 Component Patterns

#### Gateway Selector Component

```typescript
// components/common/GatewaySelector.tsx
import { useGateways } from '@/hooks/useGateways';

interface GatewaySelectorProps {
  value: string | null;
  onChange: (gatewayId: string | null) => void;
  required?: boolean;
  allowAll?: boolean;
}

export function GatewaySelector({
  value,
  onChange,
  required = false,
  allowAll = false
}: GatewaySelectorProps) {
  const { data: gateways, isLoading } = useGateways();
  
  return (
    <select
      value={value || ''}
      onChange={(e) => onChange(e.target.value || null)}
      required={required}
      className="gateway-selector"
    >
      {!required && allowAll && (
        <option value="">All Gateways</option>
      )}
      {!required && !allowAll && (
        <option value="">Select Gateway</option>
      )}
      {gateways?.map((gateway) => (
        <option key={gateway.id} value={gateway.id}>
          {gateway.name} ({gateway.vendor})
        </option>
      ))}
    </select>
  );
}
```

#### Gateway-Scoped Dashboard

```typescript
// pages/Dashboard.tsx
import { useState } from 'react';
import { GatewaySelector } from '@/components/common/GatewaySelector';
import { ApiSelector } from '@/components/common/ApiSelector';
import { useMetrics } from '@/hooks/useMetrics';

export function Dashboard() {
  const [selectedGateway, setSelectedGateway] = useState<string | null>(null);
  const [selectedApi, setSelectedApi] = useState<string | null>(null);
  
  const { data: metrics, isLoading } = useMetrics({
    gatewayId: selectedGateway,
    apiId: selectedApi,
    enabled: !!selectedGateway, // Only fetch when gateway is selected
  });
  
  return (
    <div className="dashboard">
      <div className="filters">
        <GatewaySelector
          value={selectedGateway}
          onChange={(id) => {
            setSelectedGateway(id);
            setSelectedApi(null); // Reset API when gateway changes
          }}
          required
        />
        
        {selectedGateway && (
          <ApiSelector
            gatewayId={selectedGateway}
            value={selectedApi}
            onChange={setSelectedApi}
          />
        )}
      </div>
      
      {!selectedGateway && (
        <div className="empty-state">
          Please select a gateway to view metrics
        </div>
      )}
      
      {selectedGateway && isLoading && <LoadingSpinner />}
      
      {selectedGateway && metrics && (
        <MetricsDisplay metrics={metrics} />
      )}
    </div>
  );
}
```

### 5.2 API Client Patterns

```typescript
// services/metricsService.ts
import axios from 'axios';

export interface MetricsQuery {
  gatewayId: string;      // Required
  apiId?: string;         // Optional
  timeRange?: string;     // Optional
}

export const metricsService = {
  async getMetrics(query: MetricsQuery) {
    const params = new URLSearchParams({
      gateway_id: query.gatewayId,
    });
    
    if (query.apiId) {
      params.append('api_id', query.apiId);
    }
    
    if (query.timeRange) {
      params.append('time_range', query.timeRange);
    }
    
    const response = await axios.get(`/api/v1/metrics?${params}`);
    return response.data;
  },
  
  async getCrossGatewayMetrics(gatewayIds: string[], timeRange?: string) {
    const params = new URLSearchParams();
    gatewayIds.forEach(id => params.append('gateway_ids', id));
    
    if (timeRange) {
      params.append('time_range', timeRange);
    }
    
    const response = await axios.get(`/api/v1/metrics/cross-gateway?${params}`);
    return response.data;
  }
};
```

### 5.3 React Query Hooks

```typescript
// hooks/useMetrics.ts
import { useQuery } from '@tanstack/react-query';
import { metricsService } from '@/services/metricsService';

export function useMetrics(query: {
  gatewayId: string | null;
  apiId?: string | null;
  timeRange?: string;
  enabled?: boolean;
}) {
  return useQuery({
    queryKey: ['metrics', query.gatewayId, query.apiId, query.timeRange],
    queryFn: () => {
      if (!query.gatewayId) {
        throw new Error('Gateway ID is required');
      }
      
      return metricsService.getMetrics({
        gatewayId: query.gatewayId,
        apiId: query.apiId || undefined,
        timeRange: query.timeRange,
      });
    },
    enabled: query.enabled !== false && !!query.gatewayId,
  });
}
```

---

## 6. Testing Guidelines

### 6.1 Backend Tests

```python
# tests/integration/test_gateway_scoped_metrics.py
import pytest
from uuid import uuid4

@pytest.mark.asyncio
async def test_get_metrics_requires_gateway_id(metrics_service):
    """Test that metrics queries require gateway_id."""
    gateway_id = uuid4()
    
    # Should work with gateway_id
    metrics = await metrics_service.get_metrics(gateway_id=gateway_id)
    assert isinstance(metrics, list)
    
    # Should fail without gateway_id
    with pytest.raises(TypeError):
        await metrics_service.get_metrics()

@pytest.mark.asyncio
async def test_metrics_scoped_to_gateway(metrics_service, test_gateways):
    """Test that metrics are properly scoped to gateway."""
    gateway1_id = test_gateways[0].id
    gateway2_id = test_gateways[1].id
    
    # Get metrics for gateway 1
    metrics1 = await metrics_service.get_metrics(gateway_id=gateway1_id)
    
    # All metrics should belong to gateway 1
    assert all(m.gateway_id == gateway1_id for m in metrics1)
    
    # Get metrics for gateway 2
    metrics2 = await metrics_service.get_metrics(gateway_id=gateway2_id)
    
    # All metrics should belong to gateway 2
    assert all(m.gateway_id == gateway2_id for m in metrics2)
    
    # Metrics should not overlap
    metrics1_ids = {m.id for m in metrics1}
    metrics2_ids = {m.id for m in metrics2}
    assert metrics1_ids.isdisjoint(metrics2_ids)
```

### 6.2 Frontend Tests

```typescript
// tests/components/Dashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Dashboard } from '@/pages/Dashboard';

describe('Dashboard', () => {
  it('requires gateway selection before showing metrics', async () => {
    render(<Dashboard />);
    
    // Should show empty state initially
    expect(screen.getByText(/select a gateway/i)).toBeInTheDocument();
    
    // Should not show metrics
    expect(screen.queryByTestId('metrics-display')).not.toBeInTheDocument();
  });
  
  it('loads metrics after gateway selection', async () => {
    const user = userEvent.setup();
    render(<Dashboard />);
    
    // Select gateway
    const gatewaySelector = screen.getByRole('combobox', { name: /gateway/i });
    await user.selectOptions(gatewaySelector, 'gateway-1');
    
    // Should load and display metrics
    await waitFor(() => {
      expect(screen.getByTestId('metrics-display')).toBeInTheDocument();
    });
  });
  
  it('resets API selection when gateway changes', async () => {
    const user = userEvent.setup();
    render(<Dashboard />);
    
    // Select gateway and API
    const gatewaySelector = screen.getByRole('combobox', { name: /gateway/i });
    await user.selectOptions(gatewaySelector, 'gateway-1');
    
    const apiSelector = screen.getByRole('combobox', { name: /api/i });
    await user.selectOptions(apiSelector, 'api-1');
    
    // Change gateway
    await user.selectOptions(gatewaySelector, 'gateway-2');
    
    // API selection should be reset
    expect(apiSelector).toHaveValue('');
  });
});
```

---

## 7. Common Patterns

### 7.1 Gateway Context Provider

```typescript
// contexts/GatewayContext.tsx
import { createContext, useContext, useState, ReactNode } from 'react';

interface GatewayContextValue {
  selectedGateway: string | null;
  setSelectedGateway: (id: string | null) => void;
}

const GatewayContext = createContext<GatewayContextValue | undefined>(undefined);

export function GatewayProvider({ children }: { children: ReactNode }) {
  const [selectedGateway, setSelectedGateway] = useState<string | null>(null);
  
  return (
    <GatewayContext.Provider value={{ selectedGateway, setSelectedGateway }}>
      {children}
    </GatewayContext.Provider>
  );
}

export function useGatewayContext() {
  const context = useContext(GatewayContext);
  if (!context) {
    throw new Error('useGatewayContext must be used within GatewayProvider');
  }
  return context;
}
```

### 7.2 Gateway-Scoped Data Fetching

```python
# app/services/base_service.py
from typing import Optional, List
from uuid import UUID

class BaseGatewayScopedService:
    """Base service for gateway-scoped operations."""
    
    async def get_by_gateway(
        self,
        gateway_id: UUID,
        filters: Optional[dict] = None
    ) -> List:
        """Get entities scoped to a gateway."""
        query = {"gateway_id": str(gateway_id)}
        if filters:
            query.update(filters)
        return await self.repository.find(query)
    
    async def get_by_gateway_and_api(
        self,
        gateway_id: UUID,
        api_id: UUID,
        filters: Optional[dict] = None
    ) -> List:
        """Get entities scoped to a gateway and API."""
        query = {
            "gateway_id": str(gateway_id),
            "api_id": str(api_id)
        }
        if filters:
            query.update(filters)
        return await self.repository.find(query)
```

---

## 8. Migration Checklist

Use this checklist when migrating existing features to gateway-first architecture:

### Backend Migration

- [ ] **Data Models**
  - [ ] Add `gateway_id` as required field
  - [ ] Move `gateway_id` before `api_id` in field order
  - [ ] Update field descriptions to indicate primary/secondary dimensions
  - [ ] Add validation for `gateway_id` presence

- [ ] **Repository Layer**
  - [ ] Add `find_by_gateway()` method
  - [ ] Add `find_by_gateway_and_api()` method
  - [ ] Update `find_all()` to be gateway-aware
  - [ ] Add gateway_id to all query filters

- [ ] **Service Layer**
  - [ ] Make `gateway_id` required parameter
  - [ ] Make `api_id` optional parameter
  - [ ] Update method signatures (gateway_id first)
  - [ ] Add gateway validation logic

- [ ] **API Endpoints**
  - [ ] Make `gateway_id` required query parameter
  - [ ] Make `api_id` optional query parameter
  - [ ] Update endpoint documentation
  - [ ] Add gateway validation

- [ ] **Background Jobs**
  - [ ] Update to process per-gateway
  - [ ] Add gateway context to all operations
  - [ ] Update error handling for gateway context

### Frontend Migration

- [ ] **Components**
  - [ ] Add GatewaySelector as primary filter
  - [ ] Make ApiSelector dependent on gateway selection
  - [ ] Update empty states for gateway selection
  - [ ] Add gateway context to all data displays

- [ ] **API Clients**
  - [ ] Make `gatewayId` required parameter
  - [ ] Make `apiId` optional parameter
  - [ ] Update request parameter order
  - [ ] Add gateway validation

- [ ] **React Hooks**
  - [ ] Update query keys to include gateway_id
  - [ ] Add gateway_id to dependency arrays
  - [ ] Disable queries when gateway not selected
  - [ ] Reset dependent state on gateway change

- [ ] **State Management**
  - [ ] Add gateway selection state
  - [ ] Reset API selection on gateway change
  - [ ] Persist gateway selection (optional)
  - [ ] Add gateway context provider

### Testing Migration

- [ ] **Backend Tests**
  - [ ] Add gateway-scoped test fixtures
  - [ ] Test gateway isolation
  - [ ] Test cross-gateway scenarios
  - [ ] Test gateway validation

- [ ] **Frontend Tests**
  - [ ] Test gateway selector behavior
  - [ ] Test API selector dependency
  - [ ] Test state reset on gateway change
  - [ ] Test empty states

### Documentation Migration

- [ ] Update API documentation
- [ ] Update component documentation
- [ ] Update architecture diagrams
- [ ] Update developer guides
- [ ] Update user guides

---

## Conclusion

Following this guide ensures consistent gateway-first architecture across all features. Remember:

1. **Gateway is always primary** - Never make it optional
2. **API is always secondary** - Always within gateway context
3. **Explicit is better than implicit** - Require gateway selection
4. **Test gateway isolation** - Ensure proper data scoping

For questions or clarifications, refer to:
- [Feature Scope Dimension Analysis](feature-scope-dimension-analysis.md)
- [Architecture Documentation](architecture.md)
- [API Reference](api-reference.md)

---

**Last Updated**: 2026-04-14  
**Version**: 2.0.0  
**Status**: ✅ Production Ready