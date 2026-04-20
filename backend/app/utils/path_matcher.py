"""Path matching utilities for shadow API detection.

Provides functions to parse request paths and match them against API endpoint patterns.
Supports gateway-specific routing, path parameters, and wildcards.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import unquote

from app.models.base.api import API

logger = logging.getLogger(__name__)


@dataclass
class PathComponents:
    """Components extracted from a request path."""

    gateway_prefix: str
    api_name: str
    api_version: str
    resource_path: str
    original_path: str


def parse_request_path(request_path: str) -> Optional[PathComponents]:
    """
    Parse request path into components.

    Supports multiple gateway routing formats:
    - /gateway/{apiName}/{apiVersion}/{resource_path}
    - /{apiName}/{apiVersion}/{resource_path}
    - /api/{apiVersion}/{apiName}/{resource_path}

    Args:
        request_path: Full request path from transactional log

    Returns:
        PathComponents if successfully parsed, None otherwise

    Examples:
        >>> parse_request_path("/gateway/users-api/v1/users/123/profile")
        PathComponents(
            gateway_prefix='/gateway',
            api_name='users-api',
            api_version='v1',
            resource_path='/users/123/profile',
            original_path='/gateway/users-api/v1/users/123/profile'
        )

        >>> parse_request_path("/users-api/v1/users")
        PathComponents(
            gateway_prefix='',
            api_name='users-api',
            api_version='v1',
            resource_path='/users',
            original_path='/users-api/v1/users'
        )
    """
    if not request_path:
        return None

    # URL decode the path
    decoded_path = unquote(request_path)

    # Remove query parameters
    if "?" in decoded_path:
        decoded_path = decoded_path.split("?")[0]

    # Remove trailing slash
    decoded_path = decoded_path.rstrip("/")

    # Split path into segments
    segments = [s for s in decoded_path.split("/") if s]

    if len(segments) < 3:
        logger.debug(f"Path has insufficient segments: {decoded_path}")
        return None

    # Try different parsing strategies
    components = None

    # Strategy 1: /gateway/{apiName}/{apiVersion}/{resource_path}
    if segments[0].lower() in ["gateway", "gw", "api-gateway"]:
        if len(segments) >= 3:
            components = PathComponents(
                gateway_prefix=f"/{segments[0]}",
                api_name=segments[1],
                api_version=segments[2],
                resource_path="/" + "/".join(segments[3:]) if len(segments) > 3 else "/",
                original_path=request_path,
            )

    # Strategy 2: /{apiName}/{apiVersion}/{resource_path}
    elif len(segments) >= 2:
        # Check if second segment looks like a version (v1, v2, 1.0, etc.)
        version_pattern = r"^v?\d+(\.\d+)*$"
        if re.match(version_pattern, segments[1], re.IGNORECASE):
            components = PathComponents(
                gateway_prefix="",
                api_name=segments[0],
                api_version=segments[1],
                resource_path="/" + "/".join(segments[2:]) if len(segments) > 2 else "/",
                original_path=request_path,
            )

    # Strategy 3: /api/{apiVersion}/{apiName}/{resource_path}
    if not components and segments[0].lower() == "api" and len(segments) >= 3:
        components = PathComponents(
            gateway_prefix="/api",
            api_name=segments[2],
            api_version=segments[1],
            resource_path="/" + "/".join(segments[3:]) if len(segments) > 3 else "/",
            original_path=request_path,
        )

    if components:
        logger.debug(
            f"Parsed path: {request_path} -> "
            f"api={components.api_name}, "
            f"version={components.api_version}, "
            f"resource={components.resource_path}"
        )
    else:
        logger.debug(f"Could not parse path: {request_path}")

    return components


def normalize_path_pattern(pattern: str) -> str:
    """
    Normalize path pattern to standard format.

    Converts various path parameter formats to standard {param} format:
    - :id -> {id}
    - * -> {wildcard}
    - {userId} -> {userId}

    Args:
        pattern: Path pattern to normalize

    Returns:
        Normalized pattern

    Examples:
        >>> normalize_path_pattern("/users/:id/profile")
        '/users/{id}/profile'

        >>> normalize_path_pattern("/users/*/profile")
        '/users/{wildcard}/profile'
    """
    if not pattern:
        return pattern

    # Convert :param to {param}
    pattern = re.sub(r":([a-zA-Z_][a-zA-Z0-9_]*)", r"{\1}", pattern)

    # Convert * to {wildcard}
    pattern = re.sub(r"/\*(?=/|$)", "/{wildcard}", pattern)

    return pattern


def matches_path_pattern(resource_path: str, pattern: str) -> bool:
    """
    Check if resource path matches a pattern with path parameters.

    Supports:
    - Exact matches: /users matches /users
    - Path parameters: /users/{id} matches /users/123
    - Nested paths: /users/{id}/profile matches /users/123/profile
    - Wildcards: /users/{wildcard} matches /users/anything

    Args:
        resource_path: Actual resource path from request
        pattern: Pattern to match against (with {param} placeholders)

    Returns:
        True if path matches pattern, False otherwise

    Examples:
        >>> matches_path_pattern("/users/123", "/users/{id}")
        True

        >>> matches_path_pattern("/users/123/profile", "/users/{id}/profile")
        True

        >>> matches_path_pattern("/users/123/settings", "/users/{id}/profile")
        False
    """
    if not resource_path or not pattern:
        return False

    # Normalize both paths
    resource_path = resource_path.rstrip("/")
    pattern = normalize_path_pattern(pattern.rstrip("/"))

    # Exact match
    if resource_path == pattern:
        return True

    # Split into segments
    path_segments = [s for s in resource_path.split("/") if s]
    pattern_segments = [s for s in pattern.split("/") if s]

    # Different number of segments means no match
    if len(path_segments) != len(pattern_segments):
        return False

    # Compare each segment
    for path_seg, pattern_seg in zip(path_segments, pattern_segments):
        # Pattern segment is a parameter (e.g., {id})
        if pattern_seg.startswith("{") and pattern_seg.endswith("}"):
            continue  # Any value matches

        # Exact segment match required
        if path_seg != pattern_seg:
            return False

    return True


def matches_api_endpoints(resource_path: str, api: API) -> bool:
    """
    Check if resource path matches any endpoint in API definition.

    Args:
        resource_path: Resource path from request (e.g., /users/123/profile)
        api: API object with endpoint definitions

    Returns:
        True if resource path matches any API endpoint, False otherwise

    Examples:
        >>> api = API(base_path="/api/v1/users", endpoints=[...])
        >>> matches_api_endpoints("/users/123", api)
        True
    """
    if not resource_path or not api:
        return False

    # Check if API has explicit endpoints defined
    if hasattr(api, "endpoints") and api.endpoints:
        for endpoint in api.endpoints:
            if hasattr(endpoint, "path"):
                if matches_path_pattern(resource_path, endpoint.path):
                    return True
            elif isinstance(endpoint, dict) and "path" in endpoint:
                if matches_path_pattern(resource_path, endpoint["path"]):
                    return True

    # Fallback: check against base_path
    if hasattr(api, "base_path") and api.base_path:
        # Extract resource path from base_path
        base_resource = api.base_path.split("/")[-1] if "/" in api.base_path else api.base_path
        
        # Check if resource_path starts with the base resource
        if resource_path.startswith(f"/{base_resource}"):
            return True
        
        # Check exact match
        if matches_path_pattern(resource_path, api.base_path):
            return True

    return False


def extract_api_patterns(api: API) -> List[str]:
    """
    Extract all path patterns from an API definition.

    Args:
        api: API object

    Returns:
        List of path patterns

    Examples:
        >>> api = API(base_path="/users", endpoints=[...])
        >>> extract_api_patterns(api)
        ['/users', '/users/{id}', '/users/{id}/profile']
    """
    patterns = []

    # Add base_path
    if hasattr(api, "base_path") and api.base_path:
        patterns.append(api.base_path)

    # Add explicit endpoints
    if hasattr(api, "endpoints") and api.endpoints:
        for endpoint in api.endpoints:
            if hasattr(endpoint, "path"):
                patterns.append(endpoint.path)
            elif isinstance(endpoint, dict) and "path" in endpoint:
                patterns.append(endpoint["path"])

    return patterns


def build_full_path_pattern(
    gateway_prefix: str, api_name: str, api_version: str, resource_path: str
) -> str:
    """
    Build full path pattern from components.

    Args:
        gateway_prefix: Gateway routing prefix (e.g., /gateway)
        api_name: API name (e.g., users-api)
        api_version: API version (e.g., v1)
        resource_path: Resource path (e.g., /users/{id})

    Returns:
        Full path pattern

    Examples:
        >>> build_full_path_pattern("/gateway", "users-api", "v1", "/users/{id}")
        '/gateway/users-api/v1/users/{id}'
    """
    parts = []

    if gateway_prefix:
        parts.append(gateway_prefix.strip("/"))

    parts.append(api_name)
    parts.append(api_version)

    if resource_path and resource_path != "/":
        parts.append(resource_path.lstrip("/"))

    return "/" + "/".join(parts)

# Made with Bob
