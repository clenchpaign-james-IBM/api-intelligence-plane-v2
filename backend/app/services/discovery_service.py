"""
Discovery Service

Handles API discovery from connected Gateways, including shadow API detection
and API inventory management with comprehensive error handling and retry logic.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.adapters.factory import GatewayAdapterFactory
from app.models.base.api import (
    API,
    APIStatus,
    DiscoveryMethod,
    AuthenticationType,
    Endpoint,
    IntelligenceMetadata,
    VersionInfo,
    APIType,
)
from app.models.gateway import Gateway, GatewayStatus

logger = logging.getLogger(__name__)


# Custom exception types for better error handling
class GatewayConnectionError(Exception):
    """Raised when gateway connection fails."""
    pass


class GatewayAuthenticationError(Exception):
    """Raised when gateway authentication fails."""
    pass


class GatewayTimeoutError(Exception):
    """Raised when gateway operation times out."""
    pass


class PartialDiscoveryError(Exception):
    """Raised when some APIs fail to discover but others succeed."""
    pass


class DiscoveryService:
    """Service for discovering and managing APIs from Gateways."""
    
    def __init__(
        self,
        api_repository: APIRepository,
        gateway_repository: GatewayRepository,
        adapter_factory: GatewayAdapterFactory,
    ):
        """
        Initialize the Discovery Service.
        
        Args:
            api_repository: Repository for API operations
            gateway_repository: Repository for Gateway operations
            adapter_factory: Factory for creating Gateway adapters
        """
        self.api_repo = api_repository
        self.gateway_repo = gateway_repository
        self.adapter_factory = adapter_factory
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((GatewayConnectionError, GatewayTimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _discover_gateway_with_retry(self, gateway_id: UUID) -> Dict[str, Any]:
        """
        Discover APIs from gateway with retry logic for transient failures.
        
        Args:
            gateway_id: Gateway UUID
            
        Returns:
            dict: Discovery results
            
        Raises:
            GatewayConnectionError: On connection failures
            GatewayAuthenticationError: On auth failures
            GatewayTimeoutError: On timeout
        """
        try:
            return await self.discover_gateway_apis(gateway_id)
        except ConnectionError as e:
            raise GatewayConnectionError(f"Connection failed: {e}") from e
        except (TimeoutError, asyncio.TimeoutError) as e:
            raise GatewayTimeoutError(f"Operation timed out: {e}") from e

    async def discover_all_gateways(self) -> Dict[str, Any]:
        """
        Discover APIs from all connected Gateways with comprehensive error handling.
        
        Returns:
            dict: Discovery results with statistics and detailed error information
        """
        logger.info("Starting API discovery across all gateways")
        
        # Get all connected gateways
        gateways, total = self.gateway_repo.find_connected_gateways(size=1000)
        
        if not gateways:
            logger.warning("No connected gateways found")
            return {
                "total_gateways": 0,
                "successful_gateways": 0,
                "failed_gateways": 0,
                "total_apis_discovered": 0,
                "shadow_apis_found": 0,
                "errors": [],
            }
        
        results = {
            "total_gateways": len(gateways),
            "successful_gateways": 0,
            "failed_gateways": 0,
            "total_apis_discovered": 0,
            "shadow_apis_found": 0,
            "errors": [],
        }
        
        # Discover APIs from each gateway with enhanced error handling
        for gateway in gateways:
            try:
                # Use retry wrapper for transient failures
                gateway_result = await self._discover_gateway_with_retry(gateway.id)
                results["successful_gateways"] += 1
                results["total_apis_discovered"] += gateway_result["apis_discovered"]
                results["shadow_apis_found"] += gateway_result["shadow_apis_found"]
                
                logger.info(
                    f"Successfully discovered {gateway_result['apis_discovered']} APIs "
                    f"from gateway {gateway.name} ({gateway.id})"
                )
                
            except GatewayConnectionError as e:
                logger.error(f"Connection failed for gateway {gateway.id}: {e}")
                results["failed_gateways"] += 1
                results["errors"].append({
                    "gateway_id": str(gateway.id),
                    "gateway_name": gateway.name,
                    "error_type": "connection_error",
                    "error": str(e),
                    "retryable": True,
                })
                
            except GatewayAuthenticationError as e:
                logger.error(f"Authentication failed for gateway {gateway.id}: {e}")
                results["failed_gateways"] += 1
                results["errors"].append({
                    "gateway_id": str(gateway.id),
                    "gateway_name": gateway.name,
                    "error_type": "authentication_error",
                    "error": str(e),
                    "retryable": False,
                })
                
            except GatewayTimeoutError as e:
                logger.error(f"Timeout for gateway {gateway.id}: {e}")
                results["failed_gateways"] += 1
                results["errors"].append({
                    "gateway_id": str(gateway.id),
                    "gateway_name": gateway.name,
                    "error_type": "timeout",
                    "error": str(e),
                    "retryable": True,
                })
                
            except PartialDiscoveryError as e:
                logger.warning(f"Partial discovery for gateway {gateway.id}: {e}")
                # Count as success since some APIs were discovered
                results["successful_gateways"] += 1
                results["errors"].append({
                    "gateway_id": str(gateway.id),
                    "gateway_name": gateway.name,
                    "error_type": "partial_discovery",
                    "error": str(e),
                    "retryable": False,
                })
                
            except ValueError as e:
                logger.error(f"Invalid configuration for gateway {gateway.id}: {e}")
                results["failed_gateways"] += 1
                results["errors"].append({
                    "gateway_id": str(gateway.id),
                    "gateway_name": gateway.name,
                    "error_type": "configuration_error",
                    "error": str(e),
                    "retryable": False,
                })
                
            except Exception as e:
                logger.error(f"Unexpected error for gateway {gateway.id}: {e}", exc_info=True)
                results["failed_gateways"] += 1
                results["errors"].append({
                    "gateway_id": str(gateway.id),
                    "gateway_name": gateway.name,
                    "error_type": "unknown_error",
                    "error": str(e),
                    "retryable": False,
                })
        
        logger.info(
            f"Discovery complete: {results['total_apis_discovered']} APIs discovered "
            f"from {results['successful_gateways']}/{results['total_gateways']} gateways "
            f"({results['failed_gateways']} failures)"
        )
        
        return results
    
    async def discover_gateway_apis(
        self,
        gateway_id: UUID,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Discover APIs from a specific Gateway.
        
        Args:
            gateway_id: Gateway UUID
            force_refresh: Force immediate discovery instead of using cache
            
        Returns:
            dict: Discovery results for this gateway
            
        Raises:
            ValueError: If gateway not found
            RuntimeError: If discovery fails
        """
        logger.info(f"Discovering APIs from gateway {gateway_id}")
        
        # Get gateway configuration
        gateway = self.gateway_repo.get(str(gateway_id))
        if not gateway:
            raise ValueError(f"Gateway {gateway_id} not found")
        
        # Check gateway status and handle appropriately
        if gateway.status == GatewayStatus.DISCONNECTED:
            logger.info(f"Gateway {gateway_id} is DISCONNECTED, attempting to connect...")
            # Try to connect the gateway first
            try:
                adapter = self.adapter_factory.create_adapter(gateway)
                await asyncio.wait_for(adapter.connect(), timeout=30.0)
                test_result = await adapter.test_connection()
                await adapter.disconnect()
                
                if test_result.get("connected"):
                    # Update status to CONNECTED
                    self.gateway_repo.update(str(gateway_id), {
                        "status": GatewayStatus.CONNECTED.value,
                        "last_connected_at": datetime.utcnow().isoformat(),
                        "last_error": None,
                    })
                    logger.info(f"Gateway {gateway_id} connected successfully")
                else:
                    error_msg = test_result.get("error", "Connection test failed")
                    self.gateway_repo.update(str(gateway_id), {
                        "status": GatewayStatus.ERROR.value,
                        "last_error": error_msg,
                    })
                    raise GatewayConnectionError(f"Failed to connect to gateway: {error_msg}")
            except asyncio.TimeoutError:
                error_msg = "Connection timeout"
                self.gateway_repo.update(str(gateway_id), {
                    "status": GatewayStatus.ERROR.value,
                    "last_error": error_msg,
                })
                raise GatewayTimeoutError(error_msg)
            except Exception as e:
                error_msg = str(e)
                self.gateway_repo.update(str(gateway_id), {
                    "status": GatewayStatus.ERROR.value,
                    "last_error": error_msg,
                })
                raise GatewayConnectionError(f"Failed to connect to gateway: {error_msg}")
        elif gateway.status == GatewayStatus.ERROR:
            logger.warning(f"Gateway {gateway_id} is in ERROR state, last error: {gateway.last_error}")
            # Allow discovery to proceed - it might succeed and clear the error
        
        try:
            # Create adapter for this gateway
            adapter = self.adapter_factory.create_adapter(gateway)
            
            # Connect to gateway with timeout
            try:
                await asyncio.wait_for(adapter.connect(), timeout=30.0)
            except asyncio.TimeoutError:
                raise GatewayTimeoutError(f"Connection timeout for gateway {gateway_id}")
            except ConnectionError as e:
                raise GatewayConnectionError(f"Failed to connect to gateway {gateway_id}: {e}")
            except PermissionError as e:
                raise GatewayAuthenticationError(f"Authentication failed for gateway {gateway_id}: {e}")
            
            # Discover APIs with timeout
            try:
                discovered_apis = await asyncio.wait_for(
                    adapter.discover_apis(),
                    timeout=300.0  # 5 minutes for discovery
                )
            except asyncio.TimeoutError:
                raise GatewayTimeoutError(f"API discovery timeout for gateway {gateway_id}")
            
            # Process discovered APIs
            new_apis = 0
            updated_apis = 0
            shadow_apis = 0
            failed_apis = 0
            
            for api in discovered_apis:
                try:
                    # Check if API already exists using gateway_id + api.id as unique key
                    existing_api = self.api_repo.find_by_gateway_and_api_id(
                        gateway_id=gateway_id,
                        api_id=api.id,
                    )
                    
                    if existing_api:
                        # Update existing API - update intelligence_metadata.last_seen_at
                        updates = {
                            "intelligence_metadata.last_seen_at": datetime.utcnow().isoformat(),
                            "status": APIStatus.ACTIVE.value,
                            "endpoints": [ep.model_dump() for ep in api.endpoints],
                            "methods": api.methods,
                            "updated_at": datetime.utcnow().isoformat(),
                        }
                        self.api_repo.update(str(existing_api.id), updates)
                        updated_apis += 1
                    else:
                        # Create new API using the API's own ID as document ID
                        # This ensures gateway_id + api.id uniqueness
                        self.api_repo.create(api, doc_id=str(api.id))
                        new_apis += 1
                        
                        # Check if shadow API via intelligence_metadata
                        if api.intelligence_metadata.is_shadow:
                            shadow_apis += 1
                except Exception as e:
                    logger.error(f"Failed to process API {api.name} (ID: {api.id}): {e}")
                    failed_apis += 1
                    continue
            
            # Update gateway API count and status
            total_apis = new_apis + updated_apis
            self.gateway_repo.update(str(gateway_id), {
                "api_count": total_apis,
                "status": GatewayStatus.CONNECTED.value,
                "last_connected_at": datetime.utcnow().isoformat(),
                "last_error": None,
            })
            
            # Disconnect from gateway
            await adapter.disconnect()
            
            result = {
                "gateway_id": str(gateway_id),
                "gateway_name": gateway.name,
                "apis_discovered": len(discovered_apis),
                "new_apis": new_apis,
                "updated_apis": updated_apis,
                "shadow_apis_found": shadow_apis,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            logger.info(
                f"Discovery complete for gateway {gateway_id}: "
                f"{new_apis} new, {updated_apis} updated, {shadow_apis} shadow APIs"
            )
            
            return result
            
        except (GatewayConnectionError, GatewayAuthenticationError, GatewayTimeoutError) as e:
            logger.error(f"Discovery failed for gateway {gateway_id}: {e}")
            
            # Update gateway status to ERROR with error message
            self.gateway_repo.update(str(gateway_id), {
                "status": GatewayStatus.ERROR.value,
                "last_error": str(e),
            })
            raise
        except Exception as e:
            logger.error(f"Discovery failed for gateway {gateway_id}: {e}")
            
            # Update gateway status to ERROR with error message
            self.gateway_repo.update(str(gateway_id), {
                "status": GatewayStatus.ERROR.value,
                "last_error": str(e),
            })
            
            raise RuntimeError(f"Failed to discover APIs from gateway {gateway_id}: {e}")
    
    # COMMENTED OUT: Redundant method - shadow API detection is handled by detect_shadow_apis_job
    # in backend/app/scheduler/intelligence_metadata_jobs.py
    # async def detect_shadow_apis(self, gateway_id: UUID) -> List[API]:
    #     """
    #     Detect shadow APIs by analyzing traffic patterns.
    #
    #     Shadow APIs are APIs that are receiving traffic but are not
    #     officially registered in the Gateway.
    #
    #     Args:
    #         gateway_id: Gateway UUID
    #
    #     Returns:
    #         list[API]: List of detected shadow APIs
    #     """
    #     logger.info(f"Detecting shadow APIs for gateway {gateway_id}")
    #
    #     # Get gateway
    #     gateway = self.gateway_repo.get(str(gateway_id))
    #     if not gateway:
    #         raise ValueError(f"Gateway {gateway_id} not found")
    #
    #     try:
    #         # Create adapter
    #         adapter = self.adapter_factory.create_adapter(gateway)
    #         await adapter.connect()
    #
    #         # Get all registered APIs
    #         registered_apis, _ = self.api_repo.find_by_gateway(gateway_id, size=10000)
    #         registered_paths = {api.base_path for api in registered_apis}
    #
    #         # Analyze traffic logs from OpenSearch to find unregistered endpoints
    #         shadow_apis = []
    #
    #         # Query OpenSearch for traffic logs
    #         traffic_data = await self._analyze_traffic_logs_from_opensearch(
    #             gateway_id=gateway_id,
    #             time_range_minutes=60
    #         )
    #
    #         for endpoint_data in traffic_data:
    #             path = endpoint_data.get('path')
    #             if path and path not in registered_paths:
    #                 # Build endpoints list
    #                 endpoints = endpoint_data.get('endpoints', [])
    #                 if not endpoints:
    #                     endpoints = [Endpoint(
    #                         path=path,
    #                         method='GET',
    #                         description='Discovered from traffic analysis',
    #                         parameters=[],
    #                         response_codes=[200, 404, 500],
    #                         connection_timeout=None,
    #                         read_timeout=None,
    #                     )]
    #
    #                 # Build intelligence metadata
    #                 intelligence_metadata = IntelligenceMetadata(
    #                     is_shadow=True,
    #                     discovery_method=DiscoveryMethod.TRAFFIC_ANALYSIS,
    #                     discovered_at=datetime.utcnow(),
    #                     last_seen_at=datetime.utcnow(),
    #                     health_score=endpoint_data.get('health_score', 50.0),
    #                     risk_score=None,
    #                     security_score=None,
    #                     compliance_status=None,
    #                     usage_trend=None,
    #                     has_active_predictions=False,
    #                 )
    #
    #                 # Build version info
    #                 version_info = VersionInfo(
    #                     current_version="unknown",
    #                     previous_version=None,
    #                     next_version=None,
    #                     system_version=1,
    #                     version_history=None,
    #                 )
    #
    #                 # Create shadow API with new structure
    #                 shadow_api = API(
    #                     gateway_id=gateway_id,
    #                     name=f"Shadow API: {path}",
    #                     display_name=None,
    #                     description="Discovered from traffic analysis",
    #                     icon=None,
    #                     base_path=path,
    #                     version_info=version_info,
    #                     type=APIType.REST,
    #                     maturity_state=None,
    #                     groups=[],
    #                     tags=["shadow", "unregistered"],
    #                     api_definition=None,
    #                     endpoints=endpoints,
    #                     methods=endpoint_data.get('methods', ['GET']),
    #                     authentication_type=AuthenticationType(endpoint_data.get('auth_type', 'none')),
    #                     authentication_config=None,
    #                     policy_actions=None,
    #                     ownership=None,
    #                     publishing=None,
    #                     deployments=None,
    #                     intelligence_metadata=intelligence_metadata,
    #                     status=APIStatus.ACTIVE,
    #                     is_active=True,
    #                     vendor_metadata=None,
    #                 )
    #
    #                 # Save shadow API
    #                 self.api_repo.create(shadow_api)
    #                 shadow_apis.append(shadow_api)
    #
    #         await adapter.disconnect()
    #
    #         logger.info(f"Detected {len(shadow_apis)} shadow APIs for gateway {gateway_id}")
    #         return shadow_apis
    #
    #     except Exception as e:
    #         logger.error(f"Shadow API detection failed for gateway {gateway_id}: {e}")
    #         raise
    
    def get_api_inventory(
        self,
        gateway_id: Optional[UUID] = None,
        include_shadow: bool = True,
        status: Optional[APIStatus] = None,
    ) -> tuple[List[API], int]:
        """
        Get API inventory with optional filters.
        
        Args:
            gateway_id: Optional gateway filter
            include_shadow: Include shadow APIs in results
            status: Optional status filter
            
        Returns:
            tuple[List[API], int]: List of APIs and total count
        """
        filters: Dict[str, Any] = {}
        
        if gateway_id:
            filters["gateway_id"] = gateway_id
        
        if status:
            filters["status"] = status
        
        if not include_shadow:
            filters["is_shadow"] = False
        
        if filters:
            return self.api_repo.advanced_search(filters, size=10000)
        else:
            return self.api_repo.list_all(size=10000)
    
    def get_shadow_apis(
        self,
        gateway_id: Optional[UUID] = None,
    ) -> tuple[List[API], int]:
        """
        Get all shadow APIs.
        
        Args:
            gateway_id: Optional gateway filter
            
        Returns:
            tuple[List[API], int]: List of shadow APIs and total count
        """
        if gateway_id:
            # Get shadow APIs for specific gateway
            filters = {
                "gateway_id": gateway_id,
                "is_shadow": True,
            }
            return self.api_repo.advanced_search(filters, size=10000)
        else:
            return self.api_repo.find_shadow_apis(size=10000)
    
    def get_discovery_statistics(
        self,
        gateway_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get discovery statistics.
        
        Args:
            gateway_id: Optional gateway filter
            
        Returns:
            dict: Statistics about discovered APIs
        """
        return self.api_repo.get_statistics(gateway_id=gateway_id)
    
    async def mark_api_inactive(self, api_id: UUID) -> Optional[API]:
        """
        Mark an API as inactive if it hasn't been seen recently.
        
        Args:
            api_id: API UUID
            
        Returns:
            Updated API if found, None otherwise
        """
        api = self.api_repo.get(str(api_id))
        if not api:
            return None
        
        # Check if API hasn't been seen in 24 hours
        time_since_seen = datetime.utcnow() - api.intelligence_metadata.last_seen_at
        if time_since_seen.total_seconds() > 86400:  # 24 hours
            updates = {
                "status": APIStatus.INACTIVE.value,
                "is_active": False,
                "updated_at": datetime.utcnow().isoformat(),
            }
            return self.api_repo.update(str(api_id), updates)
        
        return api
    
    # COMMENTED OUT: Helper method only used by redundant detect_shadow_apis method
    # Shadow API detection is now handled by detect_shadow_apis_job in intelligence_metadata_jobs.py
    # async def _analyze_traffic_logs_from_opensearch(
    #     self,
    #     gateway_id: UUID,
    #     time_range_minutes: int = 60,
    # ) -> List[Dict[str, Any]]:
    #     """
    #     Analyze traffic logs from OpenSearch to detect shadow APIs.
    #
    #     This method queries the gateway-logs-* indices in OpenSearch
    #     to find API endpoints that are receiving traffic but are not
    #     registered in the API inventory.
    #
    #     Args:
    #         gateway_id: Gateway UUID
    #         time_range_minutes: Time range for log analysis
    #
    #     Returns:
    #         List of endpoint data dictionaries with path, methods, and metrics
    #     """
    #     from app.db.client import get_opensearch_client
    #
    #     client = get_opensearch_client()
    #
    #     # Calculate time range
    #     end_time = datetime.utcnow()
    #     start_time = end_time - timedelta(minutes=time_range_minutes)
    #
    #     # Query for traffic logs from this gateway
    #     query = {
    #         "bool": {
    #             "must": [
    #                 {"term": {"gateway_id": str(gateway_id)}},
    #                 {
    #                     "range": {
    #                         "timestamp": {
    #                             "gte": start_time.isoformat(),
    #                             "lte": end_time.isoformat(),
    #                         }
    #                     }
    #                 },
    #             ],
    #         }
    #     }
    #
    #     # Aggregate by path to find unique endpoints
    #     aggs = {
    #         "paths": {
    #             "terms": {
    #                 "field": "path.keyword",
    #                 "size": 1000,
    #             },
    #             "aggs": {
    #                 "methods": {
    #                     "terms": {
    #                         "field": "method.keyword",
    #                         "size": 10,
    #                     }
    #                 },
    #                 "avg_response_time": {
    #                     "avg": {
    #                         "field": "response_time_ms"
    #                     }
    #                 },
    #                 "error_rate": {
    #                     "avg": {
    #                         "field": "is_error"
    #                     }
    #                 },
    #                 "request_count": {
    #                     "value_count": {
    #                         "field": "path.keyword"
    #                     }
    #                 },
    #             }
    #         }
    #     }
    #
    #     try:
    #         # Search across gateway-logs-* indices
    #         response = client.client.search(
    #             index="gateway-logs-*",
    #             body={
    #                 "query": query,
    #                 "aggs": aggs,
    #                 "size": 0,  # We only need aggregations
    #             },
    #         )
    #
    #         # Process aggregation results
    #         traffic_data = []
    #
    #         if "aggregations" in response and "paths" in response["aggregations"]:
    #             for bucket in response["aggregations"]["paths"]["buckets"]:
    #                 path = bucket["key"]
    #
    #                 # Extract methods
    #                 methods = [m["key"] for m in bucket.get("methods", {}).get("buckets", [])]
    #
    #                 # Extract metrics
    #                 avg_response_time = bucket.get("avg_response_time", {}).get("value", 100.0)
    #                 error_rate = bucket.get("error_rate", {}).get("value", 0.0)
    #                 request_count = bucket.get("request_count", {}).get("value", 0)
    #
    #                 # Calculate health score based on metrics
    #                 health_score = 100.0
    #                 if error_rate > 0.1:  # > 10% error rate
    #                     health_score -= 30
    #                 if avg_response_time > 1000:  # > 1 second
    #                     health_score -= 20
    #                 if request_count < 10:  # Low traffic
    #                     health_score -= 10
    #
    #                 traffic_data.append({
    #                     "path": path,
    #                     "methods": methods if methods else ["GET"],
    #                     "metrics": {
    #                         "response_time_p50": avg_response_time,
    #                         "response_time_p95": avg_response_time * 1.5,
    #                         "response_time_p99": avg_response_time * 2.0,
    #                         "error_rate": error_rate,
    #                         "throughput": request_count / time_range_minutes,
    #                         "availability": 100.0 - (error_rate * 100),
    #                     },
    #                     "health_score": max(0.0, health_score),
    #                     "auth_type": "none",  # Default, would need deeper analysis
    #                 })
    #
    #         logger.info(f"Analyzed traffic logs: found {len(traffic_data)} unique endpoints")
    #         return traffic_data
    #
    #     except Exception as e:
    #         logger.error(f"Failed to analyze traffic logs from OpenSearch: {e}")
    #         return []


# Made with Bob