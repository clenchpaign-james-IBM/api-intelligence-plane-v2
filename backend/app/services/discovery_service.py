"""
Discovery Service

Handles API discovery from connected Gateways, including shadow API detection
and API inventory management.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.adapters.factory import GatewayAdapterFactory
from app.models.api import API, APIStatus, DiscoveryMethod
from app.models.gateway import Gateway, GatewayStatus

logger = logging.getLogger(__name__)


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
    
    async def discover_all_gateways(self) -> Dict[str, Any]:
        """
        Discover APIs from all connected Gateways.
        
        Returns:
            dict: Discovery results with statistics
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
        
        # Discover APIs from each gateway
        for gateway in gateways:
            try:
                gateway_result = await self.discover_gateway_apis(gateway.id)
                results["successful_gateways"] += 1
                results["total_apis_discovered"] += gateway_result["apis_discovered"]
                results["shadow_apis_found"] += gateway_result["shadow_apis_found"]
            except Exception as e:
                logger.error(f"Failed to discover APIs from gateway {gateway.id}: {e}")
                results["failed_gateways"] += 1
                results["errors"].append({
                    "gateway_id": str(gateway.id),
                    "gateway_name": gateway.name,
                    "error": str(e),
                })
        
        logger.info(
            f"Discovery complete: {results['total_apis_discovered']} APIs discovered "
            f"from {results['successful_gateways']}/{results['total_gateways']} gateways"
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
        
        if gateway.status != GatewayStatus.CONNECTED:
            raise RuntimeError(f"Gateway {gateway_id} is not connected")
        
        try:
            # Create adapter for this gateway
            adapter = self.adapter_factory.create_adapter(gateway)
            
            # Connect to gateway
            await adapter.connect()
            
            # Discover APIs
            discovered_apis = await adapter.discover_apis()
            
            # Process discovered APIs
            new_apis = 0
            updated_apis = 0
            shadow_apis = 0
            
            for api in discovered_apis:
                # Check if API already exists
                existing_api = self.api_repo.find_by_base_path(
                    api.base_path,
                    gateway_id=gateway_id,
                )
                
                if existing_api:
                    # Update existing API
                    updates = {
                        "last_seen_at": datetime.utcnow().isoformat(),
                        "status": APIStatus.ACTIVE.value,
                        "endpoints": [ep.model_dump() for ep in api.endpoints],
                        "methods": api.methods,
                        "current_metrics": api.current_metrics.model_dump(),
                    }
                    self.api_repo.update(str(existing_api.id), updates)
                    updated_apis += 1
                else:
                    # Create new API
                    self.api_repo.create(api)
                    new_apis += 1
                    
                    if api.is_shadow:
                        shadow_apis += 1
            
            # Update gateway API count
            total_apis = new_apis + updated_apis
            self.gateway_repo.update_api_count(gateway_id, total_apis)
            
            # Update gateway status
            self.gateway_repo.update_status(gateway_id, GatewayStatus.CONNECTED)
            
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
            
        except Exception as e:
            logger.error(f"Discovery failed for gateway {gateway_id}: {e}")
            
            # Update gateway status to error
            self.gateway_repo.update_status(
                gateway_id,
                GatewayStatus.ERROR,
                error_message=str(e),
            )
            
            raise RuntimeError(f"Failed to discover APIs from gateway {gateway_id}: {e}")
    
    async def detect_shadow_apis(self, gateway_id: UUID) -> List[API]:
        """
        Detect shadow APIs by analyzing traffic patterns.
        
        Shadow APIs are APIs that are receiving traffic but are not
        officially registered in the Gateway.
        
        Args:
            gateway_id: Gateway UUID
            
        Returns:
            list[API]: List of detected shadow APIs
        """
        logger.info(f"Detecting shadow APIs for gateway {gateway_id}")
        
        # Get gateway
        gateway = self.gateway_repo.get(str(gateway_id))
        if not gateway:
            raise ValueError(f"Gateway {gateway_id} not found")
        
        try:
            # Create adapter
            adapter = self.adapter_factory.create_adapter(gateway)
            await adapter.connect()
            
            # Get all registered APIs
            registered_apis, _ = self.api_repo.find_by_gateway(gateway_id, size=10000)
            registered_paths = {api.base_path for api in registered_apis}
            
            # Analyze traffic logs from OpenSearch to find unregistered endpoints
            shadow_apis = []
            
            # Query OpenSearch for traffic logs
            traffic_data = await self._analyze_traffic_logs_from_opensearch(
                gateway_id=gateway_id,
                time_range_minutes=60
            )
            
            for endpoint_data in traffic_data:
                path = endpoint_data.get('path')
                if path and path not in registered_paths:
                    # Create shadow API entry with required fields
                    from app.models.api import Endpoint, CurrentMetrics, AuthenticationType
                    
                    # Build endpoints list
                    endpoints = endpoint_data.get('endpoints', [])
                    if not endpoints:
                        endpoints = [Endpoint(
                            path=path,
                            method='GET',
                            description='Discovered from traffic analysis',
                            parameters=[],
                            response_codes=[200, 404, 500],
                        )]
                    
                    # Build current metrics
                    metrics_data = endpoint_data.get('metrics', {})
                    current_metrics = CurrentMetrics(
                        response_time_p50=metrics_data.get('response_time_p50', 100.0),
                        response_time_p95=metrics_data.get('response_time_p95', 200.0),
                        response_time_p99=metrics_data.get('response_time_p99', 300.0),
                        error_rate=metrics_data.get('error_rate', 0.0),
                        throughput=metrics_data.get('throughput', 0.0),
                        availability=metrics_data.get('availability', 100.0),
                        last_error=None,
                        measured_at=datetime.utcnow(),
                    )
                    
                    shadow_api = API(
                        gateway_id=gateway_id,
                        name=f"Shadow API: {path}",
                        version=None,
                        base_path=path,
                        endpoints=endpoints,
                        methods=endpoint_data.get('methods', ['GET']),
                        authentication_type=AuthenticationType(endpoint_data.get('auth_type', 'none')),
                        authentication_config=None,
                        ownership=None,
                        is_shadow=True,
                        discovery_method=DiscoveryMethod.TRAFFIC_ANALYSIS,
                        discovered_at=datetime.utcnow(),
                        last_seen_at=datetime.utcnow(),
                        status=APIStatus.ACTIVE,
                        health_score=endpoint_data.get('health_score', 50.0),
                        current_metrics=current_metrics,
                        metadata=None,
                    )
                    
                    # Save shadow API
                    self.api_repo.create(shadow_api)
                    shadow_apis.append(shadow_api)
            
            await adapter.disconnect()
            
            logger.info(f"Detected {len(shadow_apis)} shadow APIs for gateway {gateway_id}")
            return shadow_apis
            
        except Exception as e:
            logger.error(f"Shadow API detection failed for gateway {gateway_id}: {e}")
            raise
    
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
        time_since_seen = datetime.utcnow() - api.last_seen_at
        if time_since_seen.total_seconds() > 86400:  # 24 hours
            updates = {
                "status": APIStatus.INACTIVE.value,
            }
            return self.api_repo.update(str(api_id), updates)
        
        return api
    
    async def _analyze_traffic_logs_from_opensearch(
        self,
        gateway_id: UUID,
        time_range_minutes: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Analyze traffic logs from OpenSearch to detect shadow APIs.
        
        This method queries the gateway-logs-* indices in OpenSearch
        to find API endpoints that are receiving traffic but are not
        registered in the API inventory.
        
        Args:
            gateway_id: Gateway UUID
            time_range_minutes: Time range for log analysis
            
        Returns:
            List of endpoint data dictionaries with path, methods, and metrics
        """
        from app.db.client import get_opensearch_client
        
        client = get_opensearch_client()
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_range_minutes)
        
        # Query for traffic logs from this gateway
        query = {
            "bool": {
                "must": [
                    {"term": {"gateway_id": str(gateway_id)}},
                    {
                        "range": {
                            "timestamp": {
                                "gte": start_time.isoformat(),
                                "lte": end_time.isoformat(),
                            }
                        }
                    },
                ],
            }
        }
        
        # Aggregate by path to find unique endpoints
        aggs = {
            "paths": {
                "terms": {
                    "field": "path.keyword",
                    "size": 1000,
                },
                "aggs": {
                    "methods": {
                        "terms": {
                            "field": "method.keyword",
                            "size": 10,
                        }
                    },
                    "avg_response_time": {
                        "avg": {
                            "field": "response_time_ms"
                        }
                    },
                    "error_rate": {
                        "avg": {
                            "field": "is_error"
                        }
                    },
                    "request_count": {
                        "value_count": {
                            "field": "path.keyword"
                        }
                    },
                }
            }
        }
        
        try:
            # Search across gateway-logs-* indices
            response = client.client.search(
                index="gateway-logs-*",
                body={
                    "query": query,
                    "aggs": aggs,
                    "size": 0,  # We only need aggregations
                },
            )
            
            # Process aggregation results
            traffic_data = []
            
            if "aggregations" in response and "paths" in response["aggregations"]:
                for bucket in response["aggregations"]["paths"]["buckets"]:
                    path = bucket["key"]
                    
                    # Extract methods
                    methods = [m["key"] for m in bucket.get("methods", {}).get("buckets", [])]
                    
                    # Extract metrics
                    avg_response_time = bucket.get("avg_response_time", {}).get("value", 100.0)
                    error_rate = bucket.get("error_rate", {}).get("value", 0.0)
                    request_count = bucket.get("request_count", {}).get("value", 0)
                    
                    # Calculate health score based on metrics
                    health_score = 100.0
                    if error_rate > 0.1:  # > 10% error rate
                        health_score -= 30
                    if avg_response_time > 1000:  # > 1 second
                        health_score -= 20
                    if request_count < 10:  # Low traffic
                        health_score -= 10
                    
                    traffic_data.append({
                        "path": path,
                        "methods": methods if methods else ["GET"],
                        "metrics": {
                            "response_time_p50": avg_response_time,
                            "response_time_p95": avg_response_time * 1.5,
                            "response_time_p99": avg_response_time * 2.0,
                            "error_rate": error_rate,
                            "throughput": request_count / time_range_minutes,
                            "availability": 100.0 - (error_rate * 100),
                        },
                        "health_score": max(0.0, health_score),
                        "auth_type": "none",  # Default, would need deeper analysis
                    })
            
            logger.info(f"Analyzed traffic logs: found {len(traffic_data)} unique endpoints")
            return traffic_data
            
        except Exception as e:
            logger.error(f"Failed to analyze traffic logs from OpenSearch: {e}")
            return []


# Made with Bob