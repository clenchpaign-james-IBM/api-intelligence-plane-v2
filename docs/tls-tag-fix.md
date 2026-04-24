# TLS Tag Display Fix

## Issue
API Cards in the Security page were showing "TLS" tags even when there was no actual TLS configuration policy configured for that API in the gateway. The tag was being displayed based solely on the existence of a TLS policy action with `enabled: true`, without verifying if TLS was actually enforced.

## Root Cause
The frontend component [`APISecurityCard.tsx`](../frontend/src/components/security/APISecurityCard.tsx) was checking only:
```typescript
api.policy_actions.some((action) => action.enabled && action.action_type === 'tls')
```

This logic didn't verify if the TLS policy actually had `enforce_tls: true` in its configuration.

## Backend Context
The backend has a proper utility function [`has_tls_enforced()`](../backend/app/utils/tls_config.py:178-214) that correctly checks:
1. If a TLS policy action exists
2. If the policy action is enabled
3. If `enforce_tls` is set to `true` in either:
   - `config` (TlsConfig model)
   - `vendor_config` (dict, for backward compatibility)

The [`TlsConfig`](../backend/app/models/base/policy_configs.py:466-491) model defines:
```python
class TlsConfig(BaseModel):
    enforce_tls: bool = Field(
        True, description="Require TLS for all connections"
    )
    min_tls_version: Literal["1.0", "1.1", "1.2", "1.3"] = Field(
        "1.2", description="Minimum TLS version"
    )
    # ... other fields
```

## Solution
Updated the frontend logic in [`APISecurityCard.tsx`](../frontend/src/components/security/APISecurityCard.tsx) to match the backend's validation:

```typescript
api.policy_actions.some((action) => 
  action.enabled && 
  action.action_type === 'tls' && 
  (action.config?.enforce_tls === true || action.vendor_config?.enforce_tls === true)
)
```

This ensures the TLS tag is only displayed when:
1. A TLS policy action exists
2. The policy action is enabled
3. The `enforce_tls` flag is explicitly set to `true` in the configuration

## Impact
- **Security Page**: API Cards now correctly show TLS tags only when TLS is actually enforced
- **Other Components**: No changes needed - only the Security page's APISecurityCard component displayed policy action tags

## Testing
To verify the fix:
1. Navigate to the Security page
2. Check API cards - TLS tags should only appear for APIs with actual TLS enforcement configured
3. APIs with TLS policy actions but `enforce_tls: false` should not show the TLS tag

## Related Files
- Frontend: `frontend/src/components/security/APISecurityCard.tsx`
- Backend: `backend/app/utils/tls_config.py`
- Models: `backend/app/models/base/policy_configs.py`