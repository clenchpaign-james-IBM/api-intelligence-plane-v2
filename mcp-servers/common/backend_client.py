"""
Backend HTTP Client for MCP Servers

Provides a reusable HTTP client for MCP servers to communicate with the
FastAPI backend REST API instead of directly accessing OpenSearch.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)


class BackendClient:
    """HTTP client for communicating with the FastAPI backend."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        """
        Initialize the backend client.
        
        Args:
            base_url: Base URL of the backend API (default: from BACKEND_URL env var)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://backend:8000")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Ensure base_url ends with /api/v1
        if not self.base_url.endswith("/api/v1"):
            if self.base_url.endswith("/"):
                self.base_url = f"{self.base_url}api/v1"
            else:
                self.base_url = f"{self.base_url}/api/v1"
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        
        logger.info(f"Backend client initialized with base URL: {self.base_url}")
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("Backend client closed")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the backend API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json: JSON request body
            
        Returns:
            Response data as dictionary
            
        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json,
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {method} {endpoint}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {method} {endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {method} {endpoint}: {e}")
            raise
    
    # API Discovery Endpoints
    
    async def list_apis(
        self,
        page: int = 1,
        page_size: int = 100,
        gateway_id: Optional[str] = None,
        status: Optional[str] = None,
        is_shadow: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        List all discovered APIs.
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            gateway_id: Filter by gateway ID
            status: Filter by status
            is_shadow: Filter shadow APIs
            
        Returns:
            API list response with items, total, page, page_size
        """
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        
        if gateway_id:
            params["gateway_id"] = gateway_id
        if status:
            params["status"] = status
        if is_shadow is not None:
            params["is_shadow"] = is_shadow
        
        return await self._request("GET", "/apis", params=params)
    
    async def get_api(self, api_id: str) -> Dict[str, Any]:
        """
        Get details of a specific API.
        
        Args:
            api_id: API UUID
            
        Returns:
            API details
        """
        return await self._request("GET", f"/apis/{api_id}")
    
    # Metrics Endpoints
    
    async def get_api_metrics(
        self,
        api_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        interval: str = "5m",
    ) -> Dict[str, Any]:
        """
        Get metrics for a specific API.
        
        Args:
            api_id: API UUID
            start_time: Start time (ISO 8601)
            end_time: End time (ISO 8601)
            interval: Aggregation interval (1m, 5m, 15m, 1h, 1d)
            
        Returns:
            Metrics response with time_series and aggregated data
        """
        params: Dict[str, Any] = {"interval": interval}
        
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        
        return await self._request("GET", f"/apis/{api_id}/metrics", params=params)
    
    # Prediction Endpoints
    
    async def list_predictions(
        self,
        api_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        List failure predictions.
        
        Args:
            api_id: Filter by API ID
            severity: Filter by severity
            status: Filter by status
            page: Page number
            page_size: Items per page
            
        Returns:
            Predictions list response
        """
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        
        if api_id:
            params["api_id"] = api_id
        if severity:
            params["severity"] = severity
        if status:
            params["status"] = status
        
        return await self._request("GET", "/predictions", params=params)
    
    async def generate_predictions(
        self,
        api_id: Optional[str] = None,
        min_confidence: float = 0.7,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """
        Trigger prediction generation.
        
        Args:
            api_id: Optional API ID (generates for all if not provided)
            min_confidence: Minimum confidence threshold
            use_ai: Use AI-enhanced generation
            
        Returns:
            Generation status
        """
        params: Dict[str, Any] = {
            "min_confidence": min_confidence,
            "use_ai": use_ai,
        }
        
        if api_id:
            params["api_id"] = api_id
        
        return await self._request("POST", "/predictions/generate", params=params)
    
    # Optimization Endpoints
    
    async def list_recommendations(
        self,
        api_id: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        recommendation_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        List optimization recommendations.
        
        Args:
            api_id: Filter by API ID
            priority: Filter by priority
            status: Filter by status
            recommendation_type: Filter by type
            page: Page number
            page_size: Items per page
            
        Returns:
            Recommendations list response
        """
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        
        if api_id:
            params["api_id"] = api_id
        if priority:
            params["priority"] = priority
        if status:
            params["status"] = status
        if recommendation_type:
            params["recommendation_type"] = recommendation_type
        
        return await self._request("GET", "/recommendations", params=params)
    
    async def generate_recommendations(
        self,
        api_id: str,
        min_impact: float = 10.0,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate optimization recommendations for an API.
        
        Args:
            api_id: API UUID
            min_impact: Minimum expected improvement percentage
            use_ai: Use AI-enhanced generation
            
        Returns:
            Generation results
        """
        params: Dict[str, Any] = {
            "api_id": api_id,
            "min_impact": min_impact,
            "use_ai": use_ai,
        }
        
        return await self._request("POST", "/recommendations/generate", params=params)
    
    # Rate Limiting Endpoints
    
    async def list_rate_limit_policies(
        self,
        api_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        List rate limit policies.
        
        Args:
            api_id: Filter by API ID
            status: Filter by status
            page: Page number
            page_size: Items per page
            
        Returns:
            Rate limit policies list response
        """
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        
        if api_id:
            params["api_id"] = api_id
        if status:
            params["status"] = status
        
        return await self._request("GET", "/rate-limits", params=params)
    
    async def create_rate_limit_policy(
        self,
        api_id: str,
        policy_name: str,
        policy_type: str,
        limit_thresholds: Dict[str, int],
        enforcement_action: str = "throttle",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a rate limit policy.
        
        Args:
            api_id: API UUID
            policy_name: Policy name
            policy_type: Policy type (fixed, adaptive, priority_based, burst_allowance)
            limit_thresholds: Rate limit thresholds
            enforcement_action: Enforcement action (throttle, reject, queue)
            **kwargs: Additional policy parameters
            
        Returns:
            Created policy
        """
        json_data = {
            "api_id": api_id,
            "policy_name": policy_name,
            "policy_type": policy_type,
            "limit_thresholds": limit_thresholds,
            "enforcement_action": enforcement_action,
            **kwargs,
        }
        
        return await self._request("POST", "/rate-limits", json=json_data)
    
    async def analyze_rate_limit_effectiveness(
        self,
        policy_id: str,
        analysis_period_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Analyze rate limit policy effectiveness.
        
        Args:
            policy_id: Policy UUID
            analysis_period_hours: Analysis period in hours
            
        Returns:
            Effectiveness analysis
        """
        params: Dict[str, Any] = {"analysis_period_hours": analysis_period_hours}
        
        return await self._request(
            "GET",
            f"/rate-limits/{policy_id}/effectiveness",
            params=params,
        )


# Made with Bob