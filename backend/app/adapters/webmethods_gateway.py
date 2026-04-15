"""
WebMethods API Gateway Adapter.

This adapter transforms WebMethods-specific data structures to vendor-neutral models
and provides integration with WebMethods API Gateway REST APIs.

IBM Confidential - Copyright 2024 IBM Corp.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import httpx
from opensearchpy import OpenSearch
from opensearchpy.connection import RequestsHttpConnection

from app.adapters.base import BaseGatewayAdapter
from app.db.client import get_opensearch_client
from app.db.repositories.api_repository import APIRepository
from app.models.base.api import (
    API,
    APIDefinition,
    APIStatus,
    APIType,
    AuthenticationType,
    DeploymentInfo,
    DiscoveryMethod,
    Endpoint,
    EndpointParameter,
    IntelligenceMetadata,
    MaturityState,
    OwnershipInfo,
    PolicyAction,
    PolicyActionType,
    PublishingInfo,
    VersionInfo,
)
from app.utils.webmethods.policy_parser import parse_policy_action
from app.utils.webmethods.policy_normalizer import normalize_policy_action
from app.utils.webmethods.policy_denormalizer import denormalize_policy_action
from app.utils.webmethods.policy_converter import convert_policy_action
from app.models.base.metric import Metric, TimeBucket
from app.models.base.transaction import (
    CacheStatus,
    ErrorOrigin,
    EventStatus,
    EventType,
    ExternalCall,
    ExternalCallType,
    TransactionalLog,
)
from app.models.gateway import Gateway
from app.models.webmethods.wm_api import API as WMApi
from app.models.webmethods.wm_policy import Policy as WMPolicy
from app.models.webmethods.wm_policy import PolicyAction as WMPolicyAction
from app.models.webmethods.wm_transaction import (
    CachedResponseType as WMCacheStatus,
    ErrorOrigin as WMErrorOrigin,
    ExternalCall as WMExternalCall,
    ExternalCallType as WMExternalCallType,
    RequestStatus as WMRequestStatus,
    TransactionalLog as WMTransactionalLog,
)

logger = logging.getLogger(__name__)


class WebMethodsGatewayAdapter(BaseGatewayAdapter):
    """
    Adapter for WebMethods API Gateway.

    Transforms WebMethods-specific data structures to vendor-neutral models
    and provides integration with WebMethods API Gateway REST APIs.
    """

    def __init__(self, gateway: Gateway):
        """
        Initialize WebMethods Gateway Adapter.

        Args:
            gateway: Gateway configuration containing connection details
        """
        super().__init__(gateway)
        self._client: Optional[httpx.AsyncClient] = None
        self._transactional_logs_client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> bool:
        """Establish connection to the Gateway."""
        try:
            if self._client is None:
                credentials = self.gateway.base_url_credentials
                auth: Optional[tuple[str, str]] = None
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                if credentials:
                    if credentials.type == "basic":
                        auth = (
                            credentials.username or "",
                            credentials.password or "",
                        )
                    elif credentials.type == "bearer" and credentials.token:
                        headers["Authorization"] = f"Bearer {credentials.token}"
                    elif credentials.type == "api_key" and credentials.api_key:
                        headers["x-api-key"] = credentials.api_key

                verify_ssl = (
                    self.gateway.configuration.get("verify_ssl", True)
                    if self.gateway.configuration
                    else True
                )

                self._client = httpx.AsyncClient(
                    base_url=str(self.gateway.base_url),
                    auth=auth,
                    verify=verify_ssl,
                    timeout=30.0,
                    headers=headers,
                )

            response = await self._client.get("/rest/apigateway/health")
            response.raise_for_status()
            self._connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to WebMethods Gateway: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close connection to the Gateway and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._transactional_logs_client:
            await self._transactional_logs_client.aclose()
            self._transactional_logs_client = None
        self._connected = False
        logger.info(f"Disconnected from WebMethods Gateway: {self.gateway.name}")

    async def test_connection(self) -> dict[str, Any]:
        """Test the Gateway connection and return status."""
        try:
            if not self._client:
                return {
                    "connected": False,
                    "latency_ms": 0,
                    "version": "unknown",
                    "error": "Client not initialized",
                }
            
            start_time = datetime.utcnow()
            response = await self._client.get("/rest/apigateway/health")
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "connected": response.status_code == 200,
                "latency_ms": latency,
                "version": "10.15",  # WebMethods version
                "error": None,
            }
        except Exception as e:
            return {
                "connected": False,
                "latency_ms": 0,
                "version": "unknown",
                "error": str(e),
            }

    async def discover_apis(self) -> list[API]:
        """Discover all APIs registered in the Gateway."""
        if not self._connected:
            raise RuntimeError("Not connected to Gateway")
        
        try:
            if not self._client:
                raise RuntimeError("Client not initialized")
            
            response = await self._client.get("/rest/apigateway/apis")
            response.raise_for_status()
            
            data = response.json()
            apis: list[API] = []
            api_responses = data.get("apiResponse", [])
            
            for api_response in api_responses:
                if not isinstance(api_response, dict):
                    continue
                
                api_summary = api_response.get("api")
                if not isinstance(api_summary, dict):
                    continue
                
                api_id = api_summary.get("id")
                if not api_id:
                    continue
                
                api_details = await self.get_api_details(str(api_id))
                if api_details:
                    apis.append(api_details)
            
            logger.info(f"Discovered {len(apis)} APIs from WebMethods Gateway")
            return apis
            
        except Exception as e:
            logger.error(f"Failed to discover APIs: {e}")
            raise

    async def get_api_details(self, api_id: str) -> Optional[API]:
        """Get detailed information about a specific API."""
        if not self._connected:
            raise RuntimeError("Not connected to Gateway")
        
        try:
            if not self._client:
                raise RuntimeError("Client not initialized")
            
            response = await self._client.get(f"/rest/apigateway/apis/{api_id}")
            response.raise_for_status()
            
            data = response.json()
            api_response = data.get("apiResponse", {})
            api_data = api_response.get("api") if isinstance(api_response, dict) else None
            if not isinstance(api_data, dict):
                raise ValueError(f"Unexpected WebMethods API details response for API {api_id}")
            
            wm_api = WMApi(**api_data)
            
            # Fetch and populate policy actions
            policy_actions = await self._fetch_policy_actions(wm_api)
            
            # Transform to vendor-neutral API with policy actions
            api = self._transform_to_api(wm_api)
            if policy_actions:
                api.policy_actions = policy_actions
            
            return api
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to get API details: {e}")
            raise

    async def get_transactional_logs(
        self,
        start_time: Optional[Any] = None,
        end_time: Optional[Any] = None,
    ) -> list[TransactionalLog]:
        """Retrieve raw transactional log events from the webMethods analytics OpenSearch store."""
        if not self._connected:
            raise RuntimeError("Not connected to Gateway")

        analytics_url = self.gateway.transactional_logs_url
        if not analytics_url:
            raise RuntimeError("transactional_logs_url is required for webMethods transactional logs")

        credentials = self.gateway.transactional_logs_credentials
        verify_ssl = (
            self.gateway.configuration.get("verify_ssl", True)
            if self.gateway.configuration
            else True
        )

        opensearch = OpenSearch(
            hosts=[str(analytics_url)],
            http_auth=(
                (credentials.username or "", credentials.password or "")
                if credentials and credentials.type == "basic"
                else None
            ),
            use_ssl=str(analytics_url).startswith("https://"),
            verify_certs=verify_ssl,
            connection_class=RequestsHttpConnection,
            timeout=30,
        )

        must_clauses: list[dict[str, Any]] = [{"term": {"eventType": "Transactional"}}]
        if start_time or end_time:
            range_clause: dict[str, Any] = {}
            if start_time:
                range_clause["gte"] = int(self._coerce_datetime(start_time).timestamp() * 1000)
            if end_time:
                range_clause["lte"] = int(self._coerce_datetime(end_time).timestamp() * 1000)
            must_clauses.append({"range": {"creationDate": range_clause}})

        query: dict[str, Any] = {
            "query": {"bool": {"must": must_clauses}},
            "sort": [{"creationDate": {"order": "asc"}}],
            "size": 10000,
        }

        response = opensearch.search(body=query)
        hits = response.get("hits", {}).get("hits", [])

        transactional_logs: list[TransactionalLog] = []
        for hit in hits:
            event = hit.get("_source", {})
            try:
                wm_log = WMTransactionalLog(**event)
                transactional_logs.append(self._transform_to_transactional_log(wm_log))
            except Exception as exc:
                logger.warning(f"Skipping unparseable transactional event: {exc}")

        return transactional_logs

    async def _apply_policy_action(
        self,
        api_id: str,
        policy: PolicyAction,
        policy_id: Optional[str] = None
    ) -> bool:
        """
        Apply a vendor-neutral policy action through the webMethods APIs.
        
        Args:
            api_id: The API ID to apply the policy to
            policy: The vendor-neutral PolicyAction to apply
            policy_id: Optional policy ID. If None, will be retrieved from API's policies list
            
        Returns:
            True if successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to Gateway")
        if not self._client:
            raise RuntimeError("Client not initialized")

        # Step 1 & 2: Transform and wrap vendor_payload in "policyAction" field
        vendor_payload = self._transform_from_policy_action(policy)
        create_payload = {
            "policyAction": vendor_payload
        }
        
        create_response = await self._client.post(
            "/rest/apigateway/policyActions",
            json=create_payload,
        )
        create_response.raise_for_status()

        # Step 3: Extract policyActionId from create_response.policyAction.id
        response_data = create_response.json()
        policy_action_data = response_data.get("policyAction", {})
        policy_action_id = policy_action_data.get("id") or response_data.get("id") or response_data.get("policyActionId")
        
        if not policy_action_id:
            logger.warning("No policyActionId returned from policy action creation")
            return True

        # Step 4: Get Policy object
        resolved_policy_id = await self._get_policy_id(api_id, policy_id)
        if not resolved_policy_id:
            logger.error(f"Could not resolve policy_id for API {api_id}")
            return False
        
        # Fetch the Policy object
        policy_response = await self._client.get(f"/rest/apigateway/policies/{resolved_policy_id}")
        policy_response.raise_for_status()
        policy_response_data = policy_response.json()
        
        # Extract policy from "policy" field
        policy_data = policy_response_data.get("policy", policy_response_data)
        
        # Parse the Policy object
        wm_policy = WMPolicy(**policy_data)
        
        # Step 5: Map templateKey to stageKey
        template_key = vendor_payload.get("templateKey", "")
        stage_key = self._map_template_key_to_stage_key(template_key)
        
        # Step 6: Add policyActionId to correct policyEnforcements stage
        policy_enforcements = wm_policy.policy_enforcements or []
        
        # Find existing enforcement group for this stage
        enforcement_group = None
        for group in policy_enforcements:
            if group.stage_key == stage_key:
                enforcement_group = group
                break
        
        # If no enforcement group exists for this stage, create one
        if enforcement_group is None:
            from app.models.webmethods.wm_policy import PolicyEnforcements, Enforcement
            enforcement_group = PolicyEnforcements(
                stageKey=stage_key,
                enforcements=[]
            )
            policy_enforcements.append(enforcement_group)
        
        # Add the new enforcement
        from app.models.webmethods.wm_policy import Enforcement
        new_enforcement = Enforcement(
            enforcementObjectId=policy_action_id,
            order=str(len(enforcement_group.enforcements or []) + 1),
            parentPolicyId=resolved_policy_id
        )
        
        if enforcement_group.enforcements is None:
            enforcement_group.enforcements = []
        enforcement_group.enforcements.append(new_enforcement)
        
        # Step 7: Update the Policy object
        update_payload = wm_policy.model_dump(mode="python", by_alias=True, exclude_none=True)
        
        # Wrap update_payload in "policy" field
        wrapped_payload = {
            "policy": update_payload
        }
        
        update_response = await self._client.put(
            f"/rest/apigateway/policies/{resolved_policy_id}",
            json=wrapped_payload,
        )
        update_response.raise_for_status()
        
        # Step 8: Update vendor neutral API.policy_actions in data store
        try:
            api_repo = APIRepository()
            api = api_repo.get(api_id)
            
            if api:
                # Add the new policy action to the API's policy_actions list
                if api.policy_actions is None:
                    api.policy_actions = []
                
                # Store the policy action ID in vendor_config
                if policy.vendor_config is None:
                    policy.vendor_config = {}
                policy.vendor_config["id"] = policy_action_id
                policy.vendor_config["policy_action_id"] = policy_action_id
                
                api.policy_actions.append(policy)
                
                # Update the API in the data store
                api_dict = api.model_dump(mode="json", exclude_none=True)
                api_repo.update(api_id, api_dict)
                logger.info(f"Updated API {api_id} with new policy action {policy_action_id}")
            else:
                logger.warning(f"API {api_id} not found in data store for policy action update")
        except Exception as e:
            logger.error(f"Failed to update API {api_id} policy_actions in data store: {e}")
            # Don't fail the entire operation if data store update fails
        
        return True
    
    async def _get_policy_id(self, api_id: str, policy_id: Optional[str] = None) -> Optional[str]:
        """
        Get policy ID for an API.
        
        Args:
            api_id: The API ID
            policy_id: Optional policy ID. If provided, returns it directly.
                      If None, retrieves from API's policies list.
        
        Returns:
            Policy ID or None if not found
        """
        # If policy_id is provided, return it directly
        if policy_id:
            return policy_id
        
        # Otherwise, get API from data store and extract policy_id
        try:
            api_repo = APIRepository()
            
            api = api_repo.get(api_id)
            if not api:
                logger.warning(f"API {api_id} not found in data store")
                return None
            
            # Get policy id from vendor_metadata
            vendor_metadata = api.vendor_metadata or {}
            policies = vendor_metadata.get("policies", [])
            
            if not policies or len(policies) == 0:
                logger.warning(f"No policies found in API {api_id} vendor_metadata")
                return None
            
            # Return first policy ID
            first_policy = policies[0]
            return first_policy if isinstance(first_policy, str) else str(first_policy)
            
        except Exception as e:
            logger.error(f"Failed to get policy_id from API {api_id}: {e}")
            return None
    
    def _map_template_key_to_stage_key(self, template_key: str) -> str:
        """
        Map policy action templateKey to stageKey for policy enforcement.
        
        Mapping:
        - "transport" -> "entryProtocolPolicy"
        - "IAM" -> "evaluatePolicy", "authorizeUser"
        - "requestPayloadProcessing" -> "validateAPISpec", "requestDataMasking"
        - "LMT" -> "logInvocation", "throttle", "serviceResultCache"
        - "responseProcessing" -> "responseDataMasking", "cors"
        
        Args:
            template_key: The policy action template key
            
        Returns:
            The corresponding stage key
        """
        mapping = {
            "entryProtocolPolicy": "transport",
            "evaluatePolicy": "IAM",
            "authorizeUser": "IAM",
            "validateAPISpec": "requestPayloadProcessing",
            "validateAPISpecPolicy": "requestPayloadProcessing",
            "requestDataMasking": "requestPayloadProcessing",
            "logInvocation": "LMT",
            "logInvocationPolicy": "LMT",
            "throttle": "LMT",
            "throttlePolicy": "LMT",
            "serviceResultCache": "LMT",
            "serviceResultCachePolicy": "LMT",
            "responseDataMasking": "responseProcessing",
            "cors": "responseProcessing",
            "corsPolicy": "responseProcessing",
        }
        
        return mapping.get(template_key, "request")

    async def _verify_policy_applied(self, api_id: str, policy_type: PolicyActionType) -> bool:
        """Verify that a policy was successfully applied to an API.
        
        Args:
            api_id: API identifier
            policy_type: Type of policy to verify
            
        Returns:
            bool: True if policy is present in API, False otherwise
        """
        try:
            # Re-read the API to verify policy application
            updated_api = await self.get_api_details(api_id)
            
            if not updated_api:
                logger.error(f"Failed to verify policy: API {api_id} not found after policy application")
                return False
            
            # Check if policy is present in policy_actions
            policy_found = any(
                p.action_type == policy_type 
                for p in updated_api.policy_actions or []
            )
            
            if not policy_found:
                logger.error(
                    f"Policy verification failed: {policy_type.value} "
                    f"not found in API {api_id} after application"
                )
                return False
            
            logger.info(f"Policy {policy_type.value} verified on API {api_id}")
            return True
            
        except Exception as e:
            logger.error(f"Policy verification error for API {api_id}: {e}")
            return False

    # Policy application methods (vendor-neutral policy actions)
    async def apply_rate_limit_policy(self, api_id: str, policy: PolicyAction) -> bool:
        """Apply a rate limiting policy to an API."""
        return await self._apply_policy_action(api_id, policy)

    async def remove_rate_limit_policy(self, api_id: str) -> bool:
        """Remove rate limiting policy from an API."""
        return True

    async def apply_caching_policy(self, api_id: str, policy: PolicyAction) -> bool:
        """Apply a caching policy to an API with verification."""
        success = await self._apply_policy_action(api_id, policy)
        if success:
            return await self._verify_policy_applied(api_id, PolicyActionType.CACHING)
        return False

    async def remove_caching_policy(self, api_id: str) -> bool:
        """Remove caching policy from an API."""
        return True

    async def apply_compression_policy(self, api_id: str, policy: PolicyAction) -> bool:
        """Apply a compression policy to an API with verification."""
        success = await self._apply_policy_action(api_id, policy)
        if success:
            return await self._verify_policy_applied(api_id, PolicyActionType.COMPRESSION)
        return False

    async def remove_compression_policy(self, api_id: str) -> bool:
        """Remove compression policy from an API."""
        return True

    async def apply_authentication_policy(self, api_id: str, policy: PolicyAction) -> bool:
        """Apply authentication policy to an API with verification."""
        success = await self._apply_policy_action(api_id, policy)
        if success:
            return await self._verify_policy_applied(api_id, PolicyActionType.AUTHENTICATION)
        return False

    async def apply_authorization_policy(self, api_id: str, policy: PolicyAction) -> bool:
        """Apply authorization policy to an API with verification."""
        success = await self._apply_policy_action(api_id, policy)
        if success:
            return await self._verify_policy_applied(api_id, PolicyActionType.AUTHORIZATION)
        return False

    async def apply_tls_policy(self, api_id: str, policy: PolicyAction) -> bool:
        """Apply TLS/SSL policy to an API with verification."""
        success = await self._apply_policy_action(api_id, policy)
        if success:
            return await self._verify_policy_applied(api_id, PolicyActionType.TLS)
        return False

    async def apply_cors_policy(self, api_id: str, policy: PolicyAction) -> bool:
        """Apply CORS policy to an API with verification."""
        success = await self._apply_policy_action(api_id, policy)
        if success:
            return await self._verify_policy_applied(api_id, PolicyActionType.CORS)
        return False

    async def apply_validation_policy(self, api_id: str, policy: PolicyAction) -> bool:
        """Apply input validation policy to an API with verification."""
        success = await self._apply_policy_action(api_id, policy)
        if success:
            return await self._verify_policy_applied(api_id, PolicyActionType.VALIDATION)
        return False

    async def apply_security_headers_policy(self, api_id: str, policy: PolicyAction) -> bool:
        """Apply security headers policy to an API with verification."""
        success = await self._apply_policy_action(api_id, policy)
        if success:
            # Security headers use CUSTOM policy type as there's no specific enum value
            return await self._verify_policy_applied(api_id, PolicyActionType.CUSTOM)
        return False

    async def get_gateway_health(self) -> dict[str, Any]:
        """Get Gateway health status and metrics."""
        return {
            "status": "healthy",
            "uptime_seconds": 0,
            "total_apis": 0,
            "total_requests": 0,
            "error_rate": 0.0,
        }

    async def get_capabilities(self) -> list[str]:
        """Get list of capabilities supported by this Gateway."""
        return [
            "api_discovery",
            "metrics_collection",
            "policy_management",
            "log_collection",
        ]

    def _build_endpoints(self, wm_api: WMApi) -> list[Endpoint]:
        """Build vendor-neutral endpoints from webMethods path definitions."""
        path_items = getattr(wm_api, "paths", None) or {}
        endpoints: list[Endpoint] = []

        for path, path_item in path_items.items():
            for method in ["get", "post", "put", "delete", "patch", "options", "head", "trace"]:
                operation = getattr(path_item, method, None) if path_item else None
                if not operation:
                    continue

                response_codes = []
                if operation.responses:
                    for code in operation.responses.keys():
                        try:
                            response_codes.append(int(code))
                        except (TypeError, ValueError):
                            continue

                parameters = []
                for parameter in operation.parameters or []:
                    parameters.append(
                        {
                            "name": parameter.name or "unknown",
                            "type": getattr(parameter, "in_", None) or "query",
                            "data_type": getattr(parameter, "type", None) or "string",
                            "required": bool(parameter.required),
                            "description": parameter.description,
                        }
                    )

                endpoints.append(
                    Endpoint(
                        path=path,
                        method=method.upper(),
                        description=operation.description or operation.summary,
                        parameters=parameters,
                        response_codes=response_codes,
                        connection_timeout=None,
                        read_timeout=None,
                    )
                )

        if endpoints:
            return endpoints

        return [
            Endpoint(
                path=getattr(wm_api, "base_path", "/") or "/",
                method="GET",
                description=getattr(wm_api, "api_description", None),
                parameters=[],
                response_codes=[],
                connection_timeout=None,
                read_timeout=None,
            )
        ]

    def _map_policy_action_type(self, template_key: Optional[str]) -> PolicyActionType:
        """Map webMethods template keys to vendor-neutral policy action types."""
        mapping = {
            "evaluatePolicy": PolicyActionType.AUTHENTICATION,
            "authorizeUser": PolicyActionType.AUTHORIZATION,
            "throttlePolicy": PolicyActionType.RATE_LIMITING,
            "serviceResultCache": PolicyActionType.CACHING,
            "serviceResultCachePolicy": PolicyActionType.CACHING,
            "responseCompression": PolicyActionType.COMPRESSION,
            "cors": PolicyActionType.CORS,
            "corsPolicy": PolicyActionType.CORS,
            "entryProtocolPolicy": PolicyActionType.TLS,
            "validateAPISpecPolicy": PolicyActionType.VALIDATION,
            "logInvocationPolicy": PolicyActionType.LOGGING,
        }
        return mapping.get(template_key or "", PolicyActionType.CUSTOM)

    def _map_cache_status(self, value: Optional[WMCacheStatus]) -> CacheStatus:
        """Map webMethods cache status to vendor-neutral cache status."""
        if value == WMCacheStatus.CACHED:
            return CacheStatus.HIT
        if value == WMCacheStatus.PARTIAL:
            return CacheStatus.BYPASS
        if value == WMCacheStatus.NOT_CACHED:
            return CacheStatus.MISS
        return CacheStatus.DISABLED

    def _map_event_status(self, value: WMRequestStatus) -> EventStatus:
        """Map webMethods request status to vendor-neutral event status."""
        mapping = {
            WMRequestStatus.SUCCESS: EventStatus.SUCCESS,
            WMRequestStatus.FAILURE: EventStatus.FAILURE,
            WMRequestStatus.REJECTED: EventStatus.FAILURE,
            WMRequestStatus.TIMEOUT: EventStatus.TIMEOUT,
        }
        return mapping.get(value, EventStatus.PARTIAL)

    def _map_error_origin(self, value: Optional[WMErrorOrigin]) -> Optional[ErrorOrigin]:
        """Map webMethods error origin to vendor-neutral error origin."""
        if value is None:
            return None
        mapping = {
            WMErrorOrigin.BACKEND: ErrorOrigin.BACKEND,
            WMErrorOrigin.NATIVE: ErrorOrigin.BACKEND,
            WMErrorOrigin.GATEWAY: ErrorOrigin.GATEWAY,
        }
        return mapping.get(value, ErrorOrigin.GATEWAY)

    def _map_external_call_type(self, value: WMExternalCallType) -> ExternalCallType:
        """Map webMethods external call type to vendor-neutral external call type."""
        mapping = {
            WMExternalCallType.NATIVE_SERVICE_CALL: ExternalCallType.BACKEND_SERVICE,
            WMExternalCallType.REST_API_CALL: ExternalCallType.CUSTOM,
            WMExternalCallType.SOAP_SERVICE_CALL: ExternalCallType.BACKEND_SERVICE,
            WMExternalCallType.DATABASE_CALL: ExternalCallType.CUSTOM,
        }
        return mapping.get(value, ExternalCallType.CUSTOM)

    def _coerce_datetime(self, value: Any) -> datetime:
        """Convert supported time values to timezone-aware datetimes."""
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        raise TypeError(f"Unsupported datetime value: {value!r}")

    def _percentile(self, values: list[int], percentile: float) -> float:
        """Calculate a simple percentile from a list of integers."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = round((len(sorted_values) - 1) * percentile)
        return float(sorted_values[index])

    def _floor_timestamp_to_bucket(
        self, timestamp_ms: int, time_bucket: TimeBucket
    ) -> datetime:
        """Convert an epoch-millisecond timestamp to the start of a metric time bucket."""
        bucket_time = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)

        if time_bucket == TimeBucket.ONE_MINUTE:
            bucket_time = bucket_time.replace(second=0, microsecond=0)
        elif time_bucket == TimeBucket.FIVE_MINUTES:
            minute = (bucket_time.minute // 5) * 5
            bucket_time = bucket_time.replace(minute=minute, second=0, microsecond=0)
        elif time_bucket == TimeBucket.ONE_HOUR:
            bucket_time = bucket_time.replace(minute=0, second=0, microsecond=0)
        elif time_bucket == TimeBucket.ONE_DAY:
            bucket_time = bucket_time.replace(hour=0, minute=0, second=0, microsecond=0)

        return bucket_time.replace(tzinfo=None)

    def _time_bucket_seconds(self, time_bucket: TimeBucket) -> int:
        """Return the duration in seconds for a metric time bucket."""
        mapping = {
            TimeBucket.ONE_MINUTE: 60,
            TimeBucket.FIVE_MINUTES: 300,
            TimeBucket.ONE_HOUR: 3600,
            TimeBucket.ONE_DAY: 86400,
        }
        return mapping[time_bucket]

    def _aggregate_metrics_from_transactional_logs(
        self,
        logs: list[TransactionalLog],
        time_bucket: TimeBucket = TimeBucket.ONE_MINUTE,
    ) -> list[Metric]:
        """Aggregate vendor-neutral metrics from transactional logs.

        This keeps metric derivation vendor-neutral while allowing vendors like
        webMethods to source raw events from a transactional log store instead of
        a direct metrics API. Vendors with native metrics APIs can still implement
        [`collect_metrics()`](backend/app/adapters/base.py:97) directly.
        """
        if not logs:
            return []

        grouped_logs: dict[
            tuple[str, str, Optional[str], Optional[str], datetime],
            list[TransactionalLog],
        ] = defaultdict(list)

        for log in logs:
            key = (
                log.api_id,
                str(self.gateway.id),
                log.client_id or None,
                log.operation or None,
                self._floor_timestamp_to_bucket(log.timestamp, time_bucket),
            )
            grouped_logs[key].append(log)

        return [
            self._transform_to_metric(
                {
                    "logs": group,
                    "time_bucket": time_bucket,
                    "bucket_start": bucket_start,
                }
            )
            for (_, _, _, _, bucket_start), group in grouped_logs.items()
        ]

    def _get_transactional_logs_client(self) -> httpx.AsyncClient:
        """
        Return an HTTP client configured for the transactional logs endpoint.
        
        This method reuses the existing client if available, providing connection
        pooling benefits for frequent log collection (every 5 minutes per spec).
        The client is properly closed in disconnect() to prevent resource leaks.
        
        Returns:
            httpx.AsyncClient: Configured HTTP client for transactional logs
        """
        if self._transactional_logs_client:
            logger.debug("Reusing existing transactional logs client")
            return self._transactional_logs_client

        base_url = str(self.gateway.transactional_logs_url or self.gateway.base_url)
        credentials = (
            self.gateway.transactional_logs_credentials or self.gateway.base_url_credentials
        )

        auth: Optional[tuple[str, str]] = None
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if credentials:
            if credentials.type == "basic":
                auth = (
                    credentials.username or "",
                    credentials.password or "",
                )
            elif credentials.type == "bearer" and credentials.token:
                headers["Authorization"] = f"Bearer {credentials.token}"
            elif credentials.type == "api_key" and credentials.api_key:
                headers["x-api-key"] = credentials.api_key

        verify_ssl = (
            self.gateway.configuration.get("verify_ssl", True)
            if self.gateway.configuration
            else True
        )

        # Configure connection pooling for efficient reuse
        limits = httpx.Limits(
            max_keepalive_connections=5,
            max_connections=10,
            keepalive_expiry=300.0,  # 5 minutes
        )

        self._transactional_logs_client = httpx.AsyncClient(
            base_url=base_url,
            auth=auth,
            verify=verify_ssl,
            timeout=30.0,
            headers=headers,
            limits=limits,  # Enable connection pooling
        )
        
        logger.info(
            f"Created transactional logs client for {base_url} "
            f"(auth: {credentials.type if credentials else 'none'})"
        )
        
        return self._transactional_logs_client

    async def _fetch_policy_actions(self, wm_api: WMApi) -> Optional[list[PolicyAction]]:
        """
        Fetch and transform policy actions for an API.
        
        Steps:
        1. Get policy id from the first list element of "policies" in wm_api
        2. Invoke gateway resource "/rest/apigateway/policies/{policy_id}" to get the policy object
        3. Scan "policy_enforcements", get "enforcement_object_id" from all Enforcement objects
        4. enforcement_object_id is the policyActionId
        5. Invoke gateway resource "/rest/apigateway/policyActions/{policyActionId}" to fetch PolicyAction objects
        6. Convert the PolicyAction to webMethods-specific policy type using policy_parser
        7. Convert the webMethods policy to vendor-neutral PolicyAction using policy_normalizer
        8. Return list of vendor-neutral PolicyActions
        
        Args:
            wm_api: WebMethods API object
            
        Returns:
            List of vendor-neutral PolicyAction objects or None
        """
        try:
            if not self._client:
                raise RuntimeError("Client not initialized")
            
            # Step 1: Get policy id from the first policy in the API
            policies = getattr(wm_api, "policies", None) or []
            if not policies or len(policies) == 0:
                api_id = getattr(wm_api, "api_id", None) or getattr(wm_api, "apiId", "unknown")
                logger.debug(f"No policies found for API {api_id}")
                return None
            
            policy_id = policies[0] if isinstance(policies[0], str) else getattr(policies[0], "id", None)
            if not policy_id:
                api_id = getattr(wm_api, "api_id", None) or getattr(wm_api, "apiId", "unknown")
                logger.warning(f"Could not extract policy_id from API {api_id}")
                return None
            
            # Step 2: Fetch the Policy object from the gateway
            policy_response = await self._client.get(f"/rest/apigateway/policies/{policy_id}")
            policy_response.raise_for_status()
            policy_data = policy_response.json()
            
            # Parse the Policy object (extract from "policy" field)
            wm_policy = WMPolicy(**policy_data["policy"])
            
            # Step 3 & 4: Extract enforcement_object_ids (policyActionIds) from policy_enforcements
            policy_action_ids = []
            for enforcement_group in wm_policy.policy_enforcements or []:
                for enforcement in enforcement_group.enforcements or []:
                    enforcement_id = enforcement.enforcement_object_id
                    if enforcement_id:
                        policy_action_ids.append(enforcement_id)
            
            if not policy_action_ids:
                logger.debug(f"No policy action IDs found in policy {policy_id}")
                return None
            
            # Step 5, 6, 7: Fetch, parse, and normalize each PolicyAction
            normalized_actions = []
            for action_id in policy_action_ids:
                try:
                    # Step 5: Fetch PolicyAction from gateway
                    action_response = await self._client.get(f"/rest/apigateway/policyActions/{action_id}")
                    action_response.raise_for_status()
                    action_data = action_response.json()
                    
                    # Create WMPolicyAction object (extract from "policyAction" field)
                    wm_policy_action = WMPolicyAction(**action_data["policyAction"])
                    
                    # Step 6: Parse PolicyAction to webMethods-specific policy type
                    parsed_policy = parse_policy_action(wm_policy_action)
                    
                    # Step 7: Normalize to vendor-neutral PolicyAction
                    normalized_action = normalize_policy_action(parsed_policy)
                    normalized_actions.append(normalized_action)
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        logger.warning(f"PolicyAction {action_id} not found (404)")
                    else:
                        logger.error(f"Failed to fetch PolicyAction {action_id}: {e}")
                except Exception as e:
                    logger.error(f"Failed to process PolicyAction {action_id}: {e}")
                    continue
            
            # Step 8: Return the list of normalized PolicyActions
            return normalized_actions if normalized_actions else None
            
        except httpx.HTTPStatusError as e:
            api_id = getattr(wm_api, "api_id", None) or getattr(wm_api, "apiId", "unknown")
            if e.response.status_code == 404:
                logger.warning(f"Policy not found for API {api_id}")
                return None
            logger.error(f"Failed to fetch policy for API {api_id}: {e}")
            return None
        except Exception as e:
            api_id = getattr(wm_api, "api_id", None) or getattr(wm_api, "apiId", "unknown")
            logger.error(f"Failed to fetch policy actions for API {api_id}: {e}")
            return None

    # Transformation methods
    def _transform_to_api(self, vendor_data: Any) -> API:
        """Transform WebMethods API to vendor-neutral API model."""
        wm_api: WMApi = vendor_data
        now = datetime.utcnow()

        api_id = UUID(getattr(wm_api, "id", None) or getattr(wm_api, "api_id", None) or str(uuid4()))
        name = (
            getattr(wm_api, "api_name", None)
            or getattr(wm_api, "name", None)
            or getattr(wm_api, "apiName", None)
            or "Unknown API"
        )
        display_name = (
            getattr(wm_api, "api_display_name", None)
            or getattr(wm_api, "display_name", None)
            or name
        )
        description = (
            getattr(wm_api, "api_description", None)
            or getattr(getattr(wm_api, "info", None), "description", None)
            or ""
        )

        endpoints = self._build_endpoints(wm_api)
        methods = sorted({endpoint.method for endpoint in endpoints})
        base_path = getattr(wm_api, "base_path", None) or endpoints[0].path or "/"

        api_definition = None
        if getattr(wm_api, "paths", None):
            api_definition = APIDefinition(
                type="REST",
                version=getattr(getattr(wm_api, "info", None), "version", None),
                openapi_spec=wm_api.model_dump(mode="python", by_alias=True),
                swagger_version=getattr(wm_api, "swagger", None),
                base_path=base_path,
                paths={
                    k: v.model_dump(mode="python", by_alias=True)
                    for k, v in (getattr(wm_api, "paths", {}) or {}).items()
                },
                schemas=getattr(getattr(wm_api, "components", None), "schemas", None),
                security_schemes=getattr(getattr(wm_api, "components", None), "security_schemes", None),
                vendor_extensions=getattr(wm_api, "vendor_extensions", None),
            )

        authentication_type = AuthenticationType.NONE
        if getattr(wm_api, "security", None):
            authentication_type = AuthenticationType.CUSTOM

        ownership = None
        contact = getattr(getattr(wm_api, "info", None), "contact", None)
        owner = getattr(wm_api, "owner", None)
        if contact or owner:
            ownership = OwnershipInfo(
                team=owner if isinstance(owner, str) else None,
                contact=getattr(contact, "email", None),
                organization=None,
                repository=None,
                department=None,
            )

        publishing = PublishingInfo(
            published_portals=[],
            published_to_registry=bool(getattr(wm_api, "is_published", False)),
            catalog_name=getattr(wm_api, "catalog_name", None),
            catalog_id=getattr(wm_api, "catalog_id", None),
        )

        deployments: Optional[list[DeploymentInfo]] = None
        gateway_endpoint_list = getattr(wm_api, "gatewayEndPointList", None) or getattr(
            wm_api, "gateway_endpoint_list", None
        )
        if gateway_endpoint_list:
            deployments = [
                DeploymentInfo(
                    environment="default",
                    gateway_endpoints={
                        f"endpoint_{index}": endpoint
                        for index, endpoint in enumerate(gateway_endpoint_list, start=1)
                    },
                    deployed_at=None,
                    deployment_status="active",
                )
            ]

        policy_actions = []
        for policy in getattr(wm_api, "policies", None) or []:
            policy_actions.append(self._transform_to_policy_action(policy))

        maturity_state = None
        raw_maturity = getattr(wm_api, "maturityState", None) or getattr(wm_api, "maturity_state", None)
        if raw_maturity:
            try:
                maturity_state = MaturityState(raw_maturity)
            except ValueError:
                maturity_state = None

        vendor_metadata = {
            "vendor": "webmethods",
            "owner": getattr(wm_api, "owner", None),
            "maturity_state": raw_maturity,
            "deployments": getattr(wm_api, "deployments", None),
            "gateway_endpoints": gateway_endpoint_list,
            "native_endpoint": getattr(wm_api, "nativeEndpoint", None) or getattr(wm_api, "native_endpoint", None),
        }

        return API(
            id=api_id,
            gateway_id=self.gateway.id,
            name=name,
            display_name=display_name,
            description=description,
            icon=None,
            version_info=VersionInfo(
                current_version=getattr(getattr(wm_api, "info", None), "version", None)
                or getattr(wm_api, "api_version", None)
                or "1.0.0",
                previous_version=None,
                next_version=None,
                system_version=1,
                version_history=None,
            ),
            type=APIType.REST,
            maturity_state=maturity_state,
            groups=[],
            tags=[tag.name for tag in (getattr(wm_api, "tags", None) or []) if getattr(tag, "name", None)],
            base_path=base_path,
            api_definition=api_definition,
            endpoints=endpoints,
            methods=methods,
            authentication_type=authentication_type,
            authentication_config=None,
            policy_actions=policy_actions or None,
            ownership=ownership,
            publishing=publishing,
            deployments=deployments,
            intelligence_metadata=IntelligenceMetadata(
                is_shadow=False,
                discovery_method=DiscoveryMethod.GATEWAY_SYNC,
                discovered_at=now,
                last_seen_at=now,
                health_score=100.0,
                risk_score=0.0,
                security_score=100.0,
                compliance_status={},
                usage_trend="stable",
                has_active_predictions=False,
            ),
            status=APIStatus.ACTIVE,
            is_active=True,
            vendor_metadata=vendor_metadata,
            created_at=now,
            updated_at=now,
        )

    def _transform_to_metric(self, vendor_data: Any) -> Metric:
        """Transform aggregated transactional log input to vendor-neutral Metric model."""
        payload = vendor_data if isinstance(vendor_data, dict) else {"logs": vendor_data}
        logs: list[TransactionalLog] = payload.get("logs", []) or []
        time_bucket: TimeBucket = payload.get("time_bucket", TimeBucket.ONE_MINUTE)
        bucket_start: Optional[datetime] = payload.get("bucket_start")

        if not logs:
            now = datetime.utcnow()
            return Metric(
                gateway_id=self.gateway.id,
                api_id="unknown",
                application_id=None,
                operation=None,
                timestamp=(bucket_start or now).replace(second=0, microsecond=0),
                time_bucket=time_bucket,
                request_count=0,
                success_count=0,
                failure_count=0,
                timeout_count=0,
                error_rate=0.0,
                availability=100.0,
                response_time_avg=0.0,
                response_time_min=0.0,
                response_time_max=0.0,
                response_time_p50=0.0,
                response_time_p95=0.0,
                response_time_p99=0.0,
                gateway_time_avg=0.0,
                backend_time_avg=0.0,
                throughput=0.0,
                total_data_size=0,
                avg_request_size=0.0,
                avg_response_size=0.0,
                cache_hit_count=0,
                cache_miss_count=0,
                cache_bypass_count=0,
                cache_hit_rate=0.0,
                status_2xx_count=0,
                status_3xx_count=0,
                status_4xx_count=0,
                status_5xx_count=0,
                status_codes={},
                endpoint_metrics=None,
                vendor_metadata={"vendor": "webmethods", "source": "transactional_logs"},
            )

        first = logs[0]
        total_times = [log.total_time_ms for log in logs]
        gateway_times = [log.gateway_time_ms for log in logs]
        backend_times = [log.backend_time_ms for log in logs]
        request_sizes = [log.request_size for log in logs]
        response_sizes = [log.response_size for log in logs]

        success_count = sum(1 for log in logs if log.status == EventStatus.SUCCESS)
        timeout_count = sum(1 for log in logs if log.status == EventStatus.TIMEOUT)
        failure_count = len(logs) - success_count
        request_count = len(logs)
        error_rate = (failure_count / request_count) * 100 if request_count else 0.0
        availability = (success_count / request_count) * 100 if request_count else 100.0

        status_codes: dict[str, int] = {}
        for log in logs:
            code = str(log.status_code)
            status_codes[code] = status_codes.get(code, 0) + 1

        cache_hit_count = sum(1 for log in logs if log.cache_status == CacheStatus.HIT)
        cache_miss_count = sum(1 for log in logs if log.cache_status == CacheStatus.MISS)
        cache_bypass_count = sum(1 for log in logs if log.cache_status == CacheStatus.BYPASS)
        cache_total = cache_hit_count + cache_miss_count
        cache_hit_rate = (cache_hit_count / cache_total) * 100 if cache_total else 0.0

        timestamp = bucket_start or self._floor_timestamp_to_bucket(first.timestamp, time_bucket)
        bucket_seconds = self._time_bucket_seconds(time_bucket)

        return Metric(
            gateway_id=self.gateway.id,
            api_id=first.api_id,
            application_id=first.client_id,
            operation=first.operation,
            timestamp=timestamp,
            time_bucket=time_bucket,
            request_count=request_count,
            success_count=success_count,
            failure_count=failure_count,
            timeout_count=timeout_count,
            error_rate=round(error_rate, 2),
            availability=round(availability, 2),
            response_time_avg=round(mean(total_times), 2),
            response_time_min=float(min(total_times)),
            response_time_max=float(max(total_times)),
            response_time_p50=self._percentile(total_times, 0.50),
            response_time_p95=self._percentile(total_times, 0.95),
            response_time_p99=self._percentile(total_times, 0.99),
            gateway_time_avg=round(mean(gateway_times), 2),
            backend_time_avg=round(mean(backend_times), 2),
            throughput=round(request_count / bucket_seconds, 4),
            total_data_size=sum(response_sizes) + sum(request_sizes),
            avg_request_size=round(mean(request_sizes), 2),
            avg_response_size=round(mean(response_sizes), 2),
            cache_hit_count=cache_hit_count,
            cache_miss_count=cache_miss_count,
            cache_bypass_count=cache_bypass_count,
            cache_hit_rate=round(cache_hit_rate, 2),
            status_2xx_count=sum(count for code, count in status_codes.items() if code.startswith("2")),
            status_3xx_count=sum(count for code, count in status_codes.items() if code.startswith("3")),
            status_4xx_count=sum(count for code, count in status_codes.items() if code.startswith("4")),
            status_5xx_count=sum(count for code, count in status_codes.items() if code.startswith("5")),
            status_codes=status_codes,
            endpoint_metrics=None,
            vendor_metadata={
                "vendor": "webmethods",
                "source": "transactional_logs",
                "sample_size": request_count,
                "derived_from_logs": True,
            },
        )

    def _transform_to_transactional_log(self, vendor_data: Any) -> TransactionalLog:
        """Transform webMethods transactional log to vendor-neutral TransactionalLog model."""
        wm_log: WMTransactionalLog = vendor_data

        external_calls = [
            ExternalCall(
                call_type=self._map_external_call_type(call.externalCallType),
                url=call.externalURL,
                method=None,
                start_time=call.callStartTime,
                end_time=call.callEndTime,
                duration_ms=call.callDuration,
                status_code=int(call.responseCode) if str(call.responseCode).isdigit() else None,
                success=not bool(call.responseCode and str(call.responseCode).startswith(("4", "5"))),
                request_size=None,
                response_size=None,
                error_message=None,
            )
            for call in (wm_log.externalCalls or [])
        ]

        request_path = wm_log.operationName if wm_log.operationName.startswith("/") else f"/{wm_log.operationName}"

        return TransactionalLog(
            id=wm_log.id,
            event_type=EventType.TRANSACTIONAL,
            timestamp=wm_log.creationDate,
            api_id=str(wm_log.apiId),
            api_name=wm_log.apiName,
            api_version=wm_log.apiVersion,
            operation=wm_log.operationName,
            http_method=wm_log.httpMethod,
            request_path=request_path,
            request_headers=wm_log.requestHeaders,
            request_payload=wm_log.reqPayload or None,
            request_size=len((wm_log.reqPayload or "").encode("utf-8")),
            query_parameters=wm_log.queryParameters,
            status_code=int(wm_log.responseCode) if str(wm_log.responseCode).isdigit() else 0,
            response_headers=wm_log.responseHeaders,
            response_payload=wm_log.resPayload or None,
            response_size=max(wm_log.totalDataSize - len((wm_log.reqPayload or "").encode("utf-8")), 0),
            client_id=wm_log.applicationId,
            client_name=wm_log.applicationName,
            client_ip=wm_log.applicationIp,
            user_agent=wm_log.requestHeaders.get("User-Agent"),
            total_time_ms=wm_log.totalTime,
            gateway_time_ms=wm_log.gatewayTime,
            backend_time_ms=wm_log.providerTime,
            status=self._map_event_status(wm_log.status),
            correlation_id=wm_log.correlationID,
            session_id=wm_log.sessionId,
            trace_id=wm_log.correlationID,
            cache_status=self._map_cache_status(wm_log.cachedResponse),
            backend_url=wm_log.nativeURL,
            backend_method=wm_log.nativeHttpMethod,
            backend_request_headers=wm_log.nativeRequestHeaders,
            backend_response_headers=wm_log.nativeResponseHeaders,
            error_origin=self._map_error_origin(wm_log.errorOrigin),
            error_message=wm_log.resPayload if wm_log.status != WMRequestStatus.SUCCESS else None,
            error_code=str(wm_log.responseCode),
            external_calls=external_calls,
            gateway_id=str(self.gateway.id),
            gateway_node=wm_log.sourceGatewayNode,
            vendor_metadata={
                "vendor": "webmethods",
                "source_gateway": wm_log.sourceGateway,
                "tenant_id": wm_log.tenantId,
                "server_id": wm_log.serverID,
                "callback_request": wm_log.callbackRequest,
            },
        )

    def _transform_to_policy_action(self, vendor_data: Any) -> PolicyAction:
        """Transform webMethods policy or policy action to vendor-neutral PolicyAction model."""
        template_key = getattr(vendor_data, "template_key", None) or getattr(vendor_data, "templateKey", None)
        stage_key = getattr(vendor_data, "stage_key", None) or getattr(vendor_data, "stageKey", None)
        parameters = getattr(vendor_data, "parameters", None)

        names = getattr(vendor_data, "names", None) or []
        descriptions = getattr(vendor_data, "descriptions", None) or []

        raw_enabled = getattr(vendor_data, "is_active", None) if hasattr(vendor_data, "is_active") else True
        enabled = True if raw_enabled is None else bool(raw_enabled)

        return PolicyAction(
            action_type=self._map_policy_action_type(template_key),
            enabled=enabled,
            stage=stage_key or "request",
            config={
                "template_key": template_key,
            },
            vendor_config={
                "templateKey": template_key,
                "parameters": [parameter.model_dump(mode="python", by_alias=True) for parameter in parameters] if parameters else [],
            },
            name=names[0].value if names else template_key or "webMethods policy",
            description=descriptions[0].value if descriptions else None,
        )

    def _transform_from_policy_action(self, policy_action: PolicyAction) -> Any:
        """Transform vendor-neutral PolicyAction to webMethods policy action payload.
        
        This method follows a two-step conversion process:
        1. Denormalize vendor-neutral PolicyAction to webMethods-specific policy object
        2. Convert the webMethods policy object to webMethods PolicyAction format
        
        Args:
            policy_action: Vendor-neutral PolicyAction object
            
        Returns:
            Dictionary representing webMethods PolicyAction payload
        """
        # Step 1: Denormalize vendor-neutral PolicyAction to webMethods policy object
        # This converts to one of: EntryProtocolPolicy, EvaluatePolicy, AuthorizeUserPolicy, etc.
        webmethods_policy = denormalize_policy_action(policy_action)
        
        # Step 2: Convert webMethods policy object to webMethods PolicyAction format
        # This creates the final PolicyAction with proper structure (id, names, parameters, etc.)
        webmethods_policy_action = convert_policy_action(webmethods_policy)
        
        # Return as dictionary (vendor_payload)
        return webmethods_policy_action.model_dump(by_alias=True, exclude_none=True)

# Made with Bob
