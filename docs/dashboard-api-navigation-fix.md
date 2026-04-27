# Dashboard API Card Navigation Fix

## Issue
Clicking an API card in "Top Performing APIs" and "APIs Needing Attention" sections on the Dashboard page didn't navigate to the API details.

## Root Cause
The Dashboard was linking to `/apis/${api.id}`, but:
1. No route existed for individual API details (only `/apis` and `/apis/:gatewayId`)
2. The APIs page only supported internal state-based API selection, not URL-based navigation

## Solution

### 1. Added New Route in App.tsx
Added a dedicated route for API details that doesn't conflict with the gateway route:
```typescript
<Route path="/apis/detail/:apiId" element={<APIs />} />
```

This route is placed before `/apis/:gatewayId` to ensure proper matching.

### 2. Updated APIs Page (APIs.tsx)
- Added `apiId` parameter extraction from URL params
- Added `useNavigate` hook for programmatic navigation
- Added query to fetch specific API when `apiId` is present in URL
- Added `useEffect` to set selected API when loaded from URL
- Updated `handleBack` to navigate to `/apis` when coming from URL-based navigation

Key changes:
```typescript
const { gatewayId, apiId } = useParams<{ gatewayId?: string; apiId?: string }>();
const navigate = useNavigate();

// Fetch specific API if apiId is in URL
const { data: specificAPI } = useQuery({
  queryKey: ['api', apiId],
  queryFn: () => api.apis.get(apiId!),
  enabled: !!apiId,
  staleTime: 0,
});

// Set selected API when specific API is loaded from URL
useEffect(() => {
  if (apiId && specificAPI && !selectedAPI) {
    setSelectedAPI(specificAPI);
  }
}, [apiId, specificAPI, selectedAPI]);

// Handle back to list
const handleBack = () => {
  setSelectedAPI(null);
  if (apiId) {
    navigate('/apis');
  }
};
```

### 3. Updated Dashboard Links (Dashboard.tsx)
Changed API card links to use the new route pattern:
```typescript
// Before: to={`/apis/${api.id}`}
// After:  to={`/apis/detail/${api.id}`}
```

Applied to both:
- "Top Performing APIs" section (line 259)
- "APIs Needing Attention" section (line 296)

## Files Modified
1. [`frontend/src/App.tsx`](../frontend/src/App.tsx) - Added route for `/apis/detail/:apiId`
2. [`frontend/src/pages/APIs.tsx`](../frontend/src/pages/APIs.tsx) - Added URL-based API selection support
3. [`frontend/src/pages/Dashboard.tsx`](../frontend/src/pages/Dashboard.tsx) - Updated links to use new route

## Testing
To test the fix:
1. Navigate to the Dashboard page
2. Click on any API card in "Top Performing APIs" section
3. Verify it navigates to the API detail view
4. Click "Back to API List" button
5. Verify it returns to the API list
6. Repeat for "APIs Needing Attention" section

## Technical Notes
- Used `useEffect` to avoid infinite render loops when setting state based on query results
- Route order matters: `/apis/detail/:apiId` must come before `/apis/:gatewayId` to avoid conflicts
- The existing API service already had the required `get(id)` method
- Maintains backward compatibility with existing internal state-based navigation