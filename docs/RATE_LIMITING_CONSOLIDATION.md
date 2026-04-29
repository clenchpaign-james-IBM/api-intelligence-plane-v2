# Rate Limiting Consolidation

## Overview
Rate limiting is being consolidated into the optimization feature as one of three optimization recommendation types (caching, compression, rate limiting).

## What Stays (Part of Optimization)
- `backend/app/models/base/policy_configs.py` - Contains `RateLimitConfig` used in optimization recommendations
- `backend/app/services/optimization_service.py` - Handles rate limiting as one optimization type
- `backend/app/db/repositories/recommendation_repository.py` - Stores all optimization recommendations including rate limiting
- `backend/app/api/v1/optimization.py` - Single API endpoint for all optimization types

## What Gets Removed (Separate Rate Limiting Infrastructure)
1. `backend/app/models/rate_limit.py` - Separate RateLimitPolicy model
2. `backend/app/db/repositories/rate_limit_repository.py` - Separate repository
3. `backend/app/services/rate_limit_service.py` - Separate service
4. `backend/app/api/v1/rate_limits.py` - Separate API endpoints
5. `backend/app/db/schemas/rate_limit_policies.py` - Separate index schema
6. Test files and scripts specific to separate rate limiting

## Files That Need Updates
- `backend/app/main.py` - Remove rate_limits router import
- `backend/app/db/schemas/__init__.py` - Remove rate_limit_policies index
- `backend/app/db/repositories/__init__.py` - Remove RateLimitPolicyRepository export
- `backend/app/models/__init__.py` - Remove RateLimitPolicy exports
- `backend/app/services/optimization_service.py` - Remove rate_limit_service parameter (already optional)

## Migration Path
Rate limiting recommendations are now stored in the optimization_recommendations index with type="rate_limiting", using the same OptimizationRecommendation model as caching and compression recommendations.