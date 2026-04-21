"""Unit tests for path matching utilities."""

import pytest
from unittest.mock import Mock
from app.utils.path_matcher import (
    parse_request_path,
    normalize_path_pattern,
    matches_path_pattern,
    matches_api_endpoints,
    build_full_path_pattern,
    PathComponents,
)


class TestParseRequestPath:
    """Tests for parse_request_path function."""

    def test_parse_gateway_prefix_format(self):
        """Test parsing path with gateway prefix."""
        path = "/gateway/users-api/v1/users/123/profile"
        result = parse_request_path(path)
        
        assert result is not None
        assert result.gateway_prefix == "/gateway"
        assert result.api_name == "users-api"
        assert result.api_version == "v1"
        assert result.resource_path == "/users/123/profile"
        assert result.original_path == path

    def test_parse_without_gateway_prefix(self):
        """Test parsing path without gateway prefix."""
        path = "/users-api/v1/users"
        result = parse_request_path(path)
        
        assert result is not None
        assert result.gateway_prefix == ""
        assert result.api_name == "users-api"
        assert result.api_version == "v1"
        assert result.resource_path == "/users"

    def test_parse_api_prefix_format(self):
        """Test parsing path with /api prefix."""
        path = "/api/v1/users-api/users/123"
        result = parse_request_path(path)
        
        assert result is not None
        assert result.gateway_prefix == "/api"
        assert result.api_version == "v1"
        assert result.api_name == "users-api"
        assert result.resource_path == "/users/123"

    def test_parse_with_query_parameters(self):
        """Test parsing path with query parameters."""
        path = "/gateway/users-api/v1/users?page=1&limit=10"
        result = parse_request_path(path)
        
        assert result is not None
        assert result.resource_path == "/users"
        assert "?" not in result.resource_path

    def test_parse_with_trailing_slash(self):
        """Test parsing path with trailing slash."""
        path = "/gateway/users-api/v1/users/"
        result = parse_request_path(path)
        
        assert result is not None
        assert result.resource_path == "/users"

    def test_parse_url_encoded_path(self):
        """Test parsing URL-encoded path."""
        path = "/gateway/users-api/v1/users%2F123"
        result = parse_request_path(path)
        
        assert result is not None
        assert "/123" in result.resource_path

    def test_parse_version_formats(self):
        """Test parsing different version formats."""
        test_cases = [
            ("/gateway/api/v1/resource", "v1"),
            ("/gateway/api/v2.0/resource", "v2.0"),
            ("/gateway/api/1.0/resource", "1.0"),
            ("/gateway/api/V1/resource", "V1"),
        ]
        
        for path, expected_version in test_cases:
            result = parse_request_path(path)
            assert result is not None
            assert result.api_version == expected_version

    def test_parse_api_name_with_spaces(self):
        """Test parsing API name with spaces and special characters."""
        path = "/gateway/Swagger Petstore - OpenAPI 3.0/1.0.27/pet/{petId}"
        result = parse_request_path(path)
        
        assert result is not None
        assert result.gateway_prefix == "/gateway"
        assert result.api_name == "Swagger Petstore - OpenAPI 3.0"
        assert result.api_version == "1.0.27"
        assert result.resource_path == "/pet/{petId}"

    def test_parse_url_encoded_with_spaces(self):
        """Test parsing URL-encoded path with spaces."""
        path = "/gateway%2FSwagger%20Petstore%20-%20OpenAPI%203.0%2F1.0.27%2Fpet%2F%7BpetId%7D"
        result = parse_request_path(path)
        
        assert result is not None
        assert result.gateway_prefix == "/gateway"
        assert result.api_name == "Swagger Petstore - OpenAPI 3.0"
        assert result.api_version == "1.0.27"
        assert result.resource_path == "/pet/{petId}"

    def test_parse_insufficient_segments(self):
        """Test parsing path with insufficient segments."""
        path = "/gateway/users-api"
        result = parse_request_path(path)
        
        assert result is None

    def test_parse_empty_path(self):
        """Test parsing empty path."""
        result = parse_request_path("")
        assert result is None


class TestNormalizePathPattern:
    """Tests for normalize_path_pattern function."""

    def test_normalize_colon_parameters(self):
        """Test normalizing :param format to {param}."""
        pattern = "/users/:id/profile"
        result = normalize_path_pattern(pattern)
        assert result == "/users/{id}/profile"

    def test_normalize_wildcard(self):
        """Test normalizing * to {wildcard}."""
        pattern = "/users/*/profile"
        result = normalize_path_pattern(pattern)
        assert result == "/users/{wildcard}/profile"

    def test_normalize_already_normalized(self):
        """Test normalizing already normalized pattern."""
        pattern = "/users/{id}/profile"
        result = normalize_path_pattern(pattern)
        assert result == "/users/{id}/profile"

    def test_normalize_multiple_parameters(self):
        """Test normalizing multiple parameters."""
        pattern = "/users/:userId/posts/:postId"
        result = normalize_path_pattern(pattern)
        assert result == "/users/{userId}/posts/{postId}"

    def test_normalize_empty_pattern(self):
        """Test normalizing empty pattern."""
        result = normalize_path_pattern("")
        assert result == ""


class TestMatchesPathPattern:
    """Tests for matches_path_pattern function."""

    def test_exact_match(self):
        """Test exact path matching."""
        assert matches_path_pattern("/users", "/users") is True
        assert matches_path_pattern("/users/profile", "/users/profile") is True

    def test_parameter_match(self):
        """Test path parameter matching."""
        assert matches_path_pattern("/users/123", "/users/{id}") is True
        assert matches_path_pattern("/users/abc", "/users/{id}") is True

    def test_nested_parameter_match(self):
        """Test nested path parameter matching."""
        assert matches_path_pattern(
            "/users/123/profile", "/users/{id}/profile"
        ) is True

    def test_multiple_parameters(self):
        """Test multiple path parameters."""
        assert matches_path_pattern(
            "/users/123/posts/456", "/users/{userId}/posts/{postId}"
        ) is True

    def test_wildcard_match(self):
        """Test wildcard matching."""
        assert matches_path_pattern("/users/anything", "/users/{wildcard}") is True

    def test_colon_parameter_match(self):
        """Test :param format matching."""
        assert matches_path_pattern("/users/123", "/users/:id") is True

    def test_no_match_different_segments(self):
        """Test no match with different number of segments."""
        assert matches_path_pattern("/users/123", "/users") is False
        assert matches_path_pattern("/users", "/users/123") is False

    def test_no_match_different_paths(self):
        """Test no match with different paths."""
        assert matches_path_pattern("/users/123", "/posts/{id}") is False

    def test_trailing_slash_handling(self):
        """Test trailing slash handling."""
        assert matches_path_pattern("/users/", "/users") is True
        assert matches_path_pattern("/users", "/users/") is True

    def test_empty_paths(self):
        """Test empty path handling."""
        assert matches_path_pattern("", "") is False
        assert matches_path_pattern("/users", "") is False


class TestMatchesAPIEndpoints:
    """Tests for matches_api_endpoints function."""

    def test_match_with_explicit_endpoints(self):
        """Test matching with explicit endpoint definitions."""
        # Create mock API with endpoints
        api = Mock()
        api.base_path = "/api/v1/users"
        api.endpoints = [
            Mock(path="/users"),
            Mock(path="/users/{id}"),
            Mock(path="/users/{id}/profile"),
        ]
        
        assert matches_api_endpoints("/users", api) is True
        assert matches_api_endpoints("/users/123", api) is True
        assert matches_api_endpoints("/users/123/profile", api) is True
        assert matches_api_endpoints("/posts", api) is False

    def test_match_with_dict_endpoints(self):
        """Test matching with dict-based endpoints."""
        api = Mock()
        api.base_path = "/api/v1/users"
        api.endpoints = [
            {"path": "/users"},
            {"path": "/users/{id}"},
        ]
        
        assert matches_api_endpoints("/users", api) is True
        assert matches_api_endpoints("/users/123", api) is True

    def test_match_with_base_path_fallback(self):
        """Test matching using base_path fallback."""
        api = Mock()
        api.base_path = "/api/v1/users"
        api.endpoints = []
        
        # Should match paths starting with base resource
        assert matches_api_endpoints("/users", api) is True
        assert matches_api_endpoints("/users/123", api) is True

    def test_no_match_different_resource(self):
        """Test no match with different resource."""
        api = Mock()
        api.base_path = "/api/v1/users"
        api.endpoints = [Mock(path="/users/{id}")]
        
        assert matches_api_endpoints("/posts/123", api) is False

    def test_no_endpoints_attribute(self):
        """Test API without endpoints attribute."""
        api = Mock(spec=['base_path'])
        api.base_path = "/api/v1/users"
        
        assert matches_api_endpoints("/users", api) is True


class TestBuildFullPathPattern:
    """Tests for build_full_path_pattern function."""

    def test_build_with_gateway_prefix(self):
        """Test building path with gateway prefix."""
        result = build_full_path_pattern(
            "/gateway", "users-api", "v1", "/users/{id}"
        )
        assert result == "/gateway/users-api/v1/users/{id}"

    def test_build_without_gateway_prefix(self):
        """Test building path without gateway prefix."""
        result = build_full_path_pattern("", "users-api", "v1", "/users/{id}")
        assert result == "/users-api/v1/users/{id}"

    def test_build_with_root_resource(self):
        """Test building path with root resource."""
        result = build_full_path_pattern("/gateway", "users-api", "v1", "/")
        assert result == "/gateway/users-api/v1"

    def test_build_handles_slashes(self):
        """Test building path handles extra slashes."""
        result = build_full_path_pattern(
            "/gateway/", "users-api", "v1", "users/{id}"
        )
        assert result == "/gateway/users-api/v1/users/{id}"


class TestPathComponents:
    """Tests for PathComponents dataclass."""

    def test_path_components_creation(self):
        """Test creating PathComponents."""
        components = PathComponents(
            gateway_prefix="/gateway",
            api_name="users-api",
            api_version="v1",
            resource_path="/users/123",
            original_path="/gateway/users-api/v1/users/123"
        )
        
        assert components.gateway_prefix == "/gateway"
        assert components.api_name == "users-api"
        assert components.api_version == "v1"
        assert components.resource_path == "/users/123"
        assert components.original_path == "/gateway/users-api/v1/users/123"

# Made with Bob
