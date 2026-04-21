"""
Test script to verify webMethods authentication type determination from policy actions.

This script tests that authentication_type is correctly determined from policy actions
with PolicyActionType.AUTHENTICATION, not from OpenAPI security schemes.
"""

from app.models.base.api import PolicyAction, PolicyActionType, AuthenticationType
from app.models.base.policy_configs import AuthenticationConfig
from app.adapters.webmethods_gateway import WebMethodsGatewayAdapter
from app.models.gateway import Gateway, GatewayVendor, ConnectionType, GatewayCredentials
from uuid import uuid4


def test_determine_authentication_type():
    """Test the _determine_authentication_type_from_policies method."""
    
    # Create a mock gateway with all required fields
    gateway = Gateway(
        id=uuid4(),
        name="Test Gateway",
        vendor=GatewayVendor.WEBMETHODS,
        version="10.15",
        base_url="https://test.example.com",
        transactional_logs_url=None,
        connection_type=ConnectionType.REST_API,
        base_url_credentials=GatewayCredentials(
            type="basic",
            username="test",
            password="test",
            api_key=None,
            token=None
        ),
        transactional_logs_credentials=None,
        capabilities=["api_discovery"],
        last_connected_at=None,
        last_error=None,
        configuration={},
        metadata={}
    )
    
    # Create adapter instance
    adapter = WebMethodsGatewayAdapter(gateway)
    
    # Test 1: No policy actions - should return NONE
    result = adapter._determine_authentication_type_from_policies(None)
    assert result == AuthenticationType.NONE, f"Expected NONE, got {result}"
    print("✓ Test 1 passed: No policy actions returns NONE")
    
    # Test 2: Empty policy actions list - should return NONE
    result = adapter._determine_authentication_type_from_policies([])
    assert result == AuthenticationType.NONE, f"Expected NONE, got {result}"
    print("✓ Test 2 passed: Empty policy actions returns NONE")
    
    # Test 3: Policy actions without authentication - should return NONE
    non_auth_policy = PolicyAction(
        action_type=PolicyActionType.RATE_LIMITING,
        enabled=True,
        stage="request",
        name="Rate Limit",
        description=None,
        config={"max_requests": 100},
        vendor_config=None
    )
    result = adapter._determine_authentication_type_from_policies([non_auth_policy])
    assert result == AuthenticationType.NONE, f"Expected NONE, got {result}"
    print("✓ Test 3 passed: Non-auth policy actions returns NONE")
    
    # Test 4: OAuth2 authentication (structured config)
    oauth_config = AuthenticationConfig(
        auth_type="oauth2",
        allow_anonymous=False,
        oauth_provider="auth0",
        oauth_scopes=["read", "write"],
        oauth_token_endpoint=None,
        jwt_issuer=None,
        jwt_audience=None,
        jwt_public_key_url=None,
        api_key_header=None,
        api_key_query_param=None,
        cache_credentials=True,
        cache_ttl_seconds=300
    )
    oauth_policy = PolicyAction(
        action_type=PolicyActionType.AUTHENTICATION,
        enabled=True,
        stage="request",
        name="OAuth2 Auth",
        description=None,
        config=oauth_config,
        vendor_config=None
    )
    result = adapter._determine_authentication_type_from_policies([oauth_policy])
    assert result == AuthenticationType.OAUTH2, f"Expected OAUTH2, got {result}"
    print("✓ Test 4 passed: OAuth2 structured config returns OAUTH2")
    
    # Test 5: JWT authentication (structured config) - should map to OAUTH2
    jwt_config = AuthenticationConfig(
        auth_type="jwt",
        allow_anonymous=False,
        oauth_provider=None,
        oauth_scopes=None,
        oauth_token_endpoint=None,
        jwt_issuer="https://issuer.example.com",
        jwt_audience="api",
        jwt_public_key_url=None,
        api_key_header=None,
        api_key_query_param=None,
        cache_credentials=True,
        cache_ttl_seconds=300
    )
    jwt_policy = PolicyAction(
        action_type=PolicyActionType.AUTHENTICATION,
        enabled=True,
        stage="request",
        name="JWT Auth",
        description=None,
        config=jwt_config,
        vendor_config=None
    )
    result = adapter._determine_authentication_type_from_policies([jwt_policy])
    assert result == AuthenticationType.OAUTH2, f"Expected OAUTH2, got {result}"
    print("✓ Test 5 passed: JWT structured config returns OAUTH2")
    
    # Test 6: API Key authentication (structured config)
    apikey_config = AuthenticationConfig(
        auth_type="api_key",
        allow_anonymous=False,
        oauth_provider=None,
        oauth_scopes=None,
        oauth_token_endpoint=None,
        jwt_issuer=None,
        jwt_audience=None,
        jwt_public_key_url=None,
        api_key_header="X-API-Key",
        api_key_query_param=None,
        cache_credentials=True,
        cache_ttl_seconds=300
    )
    apikey_policy = PolicyAction(
        action_type=PolicyActionType.AUTHENTICATION,
        enabled=True,
        stage="request",
        name="API Key Auth",
        description=None,
        config=apikey_config,
        vendor_config=None
    )
    result = adapter._determine_authentication_type_from_policies([apikey_policy])
    assert result == AuthenticationType.API_KEY, f"Expected API_KEY, got {result}"
    print("✓ Test 6 passed: API Key structured config returns API_KEY")
    
    # Test 7: Basic authentication (structured config)
    basic_config = AuthenticationConfig(
        auth_type="basic",
        allow_anonymous=False,
        oauth_provider=None,
        oauth_scopes=None,
        oauth_token_endpoint=None,
        jwt_issuer=None,
        jwt_audience=None,
        jwt_public_key_url=None,
        api_key_header=None,
        api_key_query_param=None,
        cache_credentials=True,
        cache_ttl_seconds=300
    )
    basic_policy = PolicyAction(
        action_type=PolicyActionType.AUTHENTICATION,
        enabled=True,
        stage="request",
        name="Basic Auth",
        description=None,
        config=basic_config,
        vendor_config=None
    )
    result = adapter._determine_authentication_type_from_policies([basic_policy])
    assert result == AuthenticationType.BASIC, f"Expected BASIC, got {result}"
    print("✓ Test 7 passed: Basic structured config returns BASIC")
    
    # Test 8: Dict config with oauth2 (backward compatibility)
    dict_oauth_policy = PolicyAction(
        action_type=PolicyActionType.AUTHENTICATION,
        enabled=True,
        stage="request",
        name="OAuth2 Auth",
        description=None,
        config={"auth_type": "oauth2", "provider": "auth0"},
        vendor_config=None
    )
    result = adapter._determine_authentication_type_from_policies([dict_oauth_policy])
    assert result == AuthenticationType.OAUTH2, f"Expected OAUTH2, got {result}"
    print("✓ Test 8 passed: Dict config with oauth2 returns OAUTH2")
    
    # Test 9: Dict config with api_key (backward compatibility)
    dict_apikey_policy = PolicyAction(
        action_type=PolicyActionType.AUTHENTICATION,
        enabled=True,
        stage="request",
        name="API Key Auth",
        description=None,
        config={"auth_type": "api_key", "header": "X-API-Key"},
        vendor_config=None
    )
    result = adapter._determine_authentication_type_from_policies([dict_apikey_policy])
    assert result == AuthenticationType.API_KEY, f"Expected API_KEY, got {result}"
    print("✓ Test 9 passed: Dict config with api_key returns API_KEY")
    
    # Test 10: Dict config with basic (backward compatibility)
    dict_basic_policy = PolicyAction(
        action_type=PolicyActionType.AUTHENTICATION,
        enabled=True,
        stage="request",
        name="Basic Auth",
        description=None,
        config={"auth_type": "basic"},
        vendor_config=None
    )
    result = adapter._determine_authentication_type_from_policies([dict_basic_policy])
    assert result == AuthenticationType.BASIC, f"Expected BASIC, got {result}"
    print("✓ Test 10 passed: Dict config with basic returns BASIC")
    
    print("\n✅ All 10 tests passed!")
    print("\nSummary:")
    print("- Authentication type is correctly determined from policy actions")
    print("- Supports both structured AuthenticationConfig and dict configs")
    print("- Maps OAuth2, JWT, API Key, and Basic auth types correctly")
    print("- Returns NONE when no authentication policies are present")


if __name__ == "__main__":
    test_determine_authentication_type()

# Made with Bob
