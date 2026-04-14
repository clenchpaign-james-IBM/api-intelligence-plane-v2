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
        gateway_id: str,
        page: int = 1,
        page_size: int = 100,
        status: Optional[str] = None,
        is_shadow: Optional[bool] = None,
        health_score_min: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        List all discovered APIs for a gateway.
        
        Args:
            gateway_id: Gateway UUID (required)
            page: Page number (1-based)
            page_size: Number of items per page
            status: Filter by status
            is_shadow: Filter shadow APIs
            health_score_min: Minimum health score filter (0.0-1.0)
            
        Returns:
            API list response with items, total, page, page_size
        """
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        
        if status:
            params["status"] = status
        if is_shadow is not None:
            params["is_shadow"] = is_shadow
        if health_score_min is not None:
            params["health_score_min"] = health_score_min
        
        return await self._request("GET", f"/gateways/{gateway_id}/apis", params=params)
    
    async def get_api(self, gateway_id: str, api_id: str) -> Dict[str, Any]:
        """
        Get details of a specific API.
        
        Args:
            gateway_id: Gateway UUID
            api_id: API UUID
            
        Returns:
            API details
        """
        return await self._request("GET", f"/gateways/{gateway_id}/apis/{api_id}")
    
    async def search_apis(
        self,
        gateway_id: str,
        query: str,
        limit: int = 100,
        status: Optional[str] = None,
        is_shadow: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Search APIs using backend's full-text search within a gateway.
        
        Args:
            gateway_id: Gateway UUID
            query: Search query string
            limit: Maximum results (default: 100, max: 1000)
            status: Optional status filter
            is_shadow: Optional shadow API filter
            
        Returns:
            Search results with relevance scoring
        """
        params: Dict[str, Any] = {
            "q": query,
            "limit": limit,
        }
        
        if status:
            params["status"] = status
        if is_shadow is not None:
            params["is_shadow"] = is_shadow
        
        return await self._request("GET", f"/gateways/{gateway_id}/apis/search", params=params)
    
    # Metrics Endpoints
    
    async def get_api_metrics(
        self,
        gateway_id: str,
        api_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        interval: str = "5m",
    ) -> Dict[str, Any]:
        """
        Get metrics for a specific API.
        
        Args:
            gateway_id: Gateway UUID
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
        
        return await self._request("GET", f"/gateways/{gateway_id}/apis/{api_id}/metrics", params=params)
    
    # Prediction Endpoints
    
    async def list_predictions(
        self,
        gateway_id: str,
        api_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        List failure predictions for a gateway.
        
        Args:
            gateway_id: Gateway UUID
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
        
        return await self._request("GET", f"/gateways/{gateway_id}/predictions", params=params)
    
    async def get_prediction(self, gateway_id: str, prediction_id: str) -> Dict[str, Any]:
        """
        Get details of a specific prediction.
        
        Args:
            gateway_id: Gateway UUID
            prediction_id: Prediction UUID
            
        Returns:
            Prediction details
        """
        return await self._request("GET", f"/gateways/{gateway_id}/predictions/{prediction_id}")
    
    async def get_prediction_explanation(
        self,
        gateway_id: str,
        prediction_id: str,
    ) -> Dict[str, Any]:
        """
        Get AI explanation for a specific prediction.
        
        Args:
            gateway_id: Gateway UUID
            prediction_id: Prediction UUID
            
        Returns:
            AI explanation payload
        """
        return await self._request(
            "GET",
            f"/gateways/{gateway_id}/predictions/{prediction_id}/explanation",
        )
    
    async def get_prediction_accuracy_stats(
        self,
        gateway_id: str,
        api_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get prediction accuracy statistics for a gateway.
        
        Args:
            gateway_id: Gateway UUID
            api_id: Optional API UUID filter
            days: Number of days to analyze
            
        Returns:
            Accuracy statistics response
        """
        params: Dict[str, Any] = {"days": days}
        
        if api_id:
            params["api_id"] = api_id
        
        return await self._request(
            "GET",
            f"/gateways/{gateway_id}/predictions/stats/accuracy",
            params=params,
        )
    
    async def generate_predictions(
        self,
        gateway_id: str,
        api_id: Optional[str] = None,
        min_confidence: float = 0.7,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """
        Trigger prediction generation for a gateway.
        
        Args:
            gateway_id: Gateway UUID
            api_id: Optional API ID (generates for all APIs in gateway if not provided)
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
        
        return await self._request("POST", f"/gateways/{gateway_id}/predictions/generate", params=params)
    
    # Optimization Endpoints
    
    async def list_recommendations(
        self,
        gateway_id: str,
        api_id: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        recommendation_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        List optimization recommendations for a gateway.
        
        Args:
            gateway_id: Gateway UUID
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
        
        return await self._request("GET", f"/gateways/{gateway_id}/optimization/recommendations", params=params)
    
    async def generate_recommendations(
        self,
        gateway_id: str,
        api_id: str,
        min_impact: float = 10.0,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate optimization recommendations for an API.
        
        Args:
            gateway_id: Gateway UUID
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
        
        return await self._request("POST", f"/gateways/{gateway_id}/optimization/recommendations/generate", params=params)
    
    # Rate Limiting Endpoints
    
    async def list_rate_limit_policies(
        self,
        gateway_id: str,
        api_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        List rate limit policies for a gateway.
        
        Args:
            gateway_id: Gateway UUID
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
        
        return await self._request("GET", f"/gateways/{gateway_id}/rate-limits", params=params)
    
    async def create_rate_limit_policy(
        self,
        gateway_id: str,
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
            gateway_id: Gateway UUID
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
            "gateway_id": gateway_id,
            "api_id": api_id,
            "policy_name": policy_name,
            "policy_type": policy_type,
            "limit_thresholds": limit_thresholds,
            "enforcement_action": enforcement_action,
            **kwargs,
        }
        
        return await self._request("POST", f"/gateways/{gateway_id}/rate-limits", json=json_data)
    
    async def analyze_rate_limit_effectiveness(
        self,
        gateway_id: str,
        policy_id: str,
        analysis_period_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Analyze rate limit policy effectiveness.
        
        Args:
            gateway_id: Gateway UUID
            policy_id: Policy UUID
            analysis_period_hours: Analysis period in hours
            
        Returns:
            Effectiveness analysis
        """
        params: Dict[str, Any] = {"analysis_period_hours": analysis_period_hours}
        
        return await self._request(
            "GET",
            f"/gateways/{gateway_id}/rate-limits/{policy_id}/effectiveness",
            params=params,
        )
    # Compliance Endpoints
    
    async def scan_api_compliance(
        self,
        gateway_id: str,
        api_id: str,
        standards: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Scan API for compliance violations.
        
        Args:
            gateway_id: Gateway UUID
            api_id: API UUID to scan
            standards: Optional list of specific standards to check
                      Valid values: ["GDPR", "HIPAA", "SOC2", "PCI_DSS", "ISO_27001"]
            
        Returns:
            Scan results with violations and evidence
        """
        payload: Dict[str, Any] = {
            "gateway_id": gateway_id,
            "api_id": api_id
        }
        if standards:
            payload["standards"] = standards
        
        return await self._request("POST", f"/gateways/{gateway_id}/compliance/scan", json=payload)
    
    async def get_compliance_violations(
        self,
        gateway_id: str,
        api_id: Optional[str] = None,
        standard: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get compliance violations with optional filters for a gateway.
        
        Args:
            gateway_id: Gateway UUID
            api_id: Optional API UUID filter
            standard: Optional compliance standard filter
            severity: Optional severity filter
            status: Optional status filter
            limit: Maximum results
            
        Returns:
            List of compliance violations
        """
        params: Dict[str, Any] = {"limit": limit}
        
        if api_id:
            params["api_id"] = api_id
        if standard:
            params["standard"] = standard
        if severity:
            params["severity"] = severity
        if status:
            params["status"] = status
        
        return await self._request("GET", f"/gateways/{gateway_id}/compliance/violations", params=params)
    
    async def get_compliance_posture(
        self,
        gateway_id: str,
        api_id: Optional[str] = None,
        standard: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get compliance posture metrics for a gateway.
        
        Args:
            gateway_id: Gateway UUID
            api_id: Optional API UUID filter
            standard: Optional compliance standard filter
            
        Returns:
            Compliance posture metrics and scores
        """
        params: Dict[str, Any] = {}
        
        if api_id:
            params["api_id"] = api_id
        if standard:
            params["standard"] = standard
        
        return await self._request("GET", f"/gateways/{gateway_id}/compliance/posture", params=params)
    
    async def generate_audit_report(
        self,
        gateway_id: str,
        api_id: Optional[str] = None,
        standard: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive audit report for a gateway.
        
        Args:
            gateway_id: Gateway UUID
            api_id: Optional API UUID filter
            standard: Optional compliance standard filter
            start_date: Report start date (ISO format)
            end_date: Report end date (ISO format)
            
        Returns:
            Comprehensive audit report with evidence
        """
        payload: Dict[str, Any] = {}
        
        if api_id:
            payload["api_id"] = api_id
        if standard:
            payload["standard"] = standard
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
        
        return await self._request("POST", f"/gateways/{gateway_id}/compliance/reports/audit", json=payload)



# Made with Bob