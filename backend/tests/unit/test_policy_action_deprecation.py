"""
Unit tests for PolicyAction structured config enforcement.

Tests that dict-based configs are rejected and only structured configs are allowed.
"""

import pytest
from pydantic import ValidationError

from app.models.base.api import PolicyAction, PolicyActionType
from app.models.base.policy_configs import RateLimitConfig, AuthenticationConfig


def test_dict_config_raises_validation_error():
    """Test that dict-based config raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        # Attempt to create PolicyAction with dict config (no longer supported)
        policy = PolicyAction(
            action_type=PolicyActionType.RATE_LIMITING,
            config={"requests_per_minute": 1000}
        )
    
    # Check that the error message is helpful
    error_message = str(exc_info.value)
    assert "dict-based config is no longer supported" in error_message.lower()
    assert "RateLimitConfig" in error_message


def test_structured_config_works():
    """Test that structured config works without errors."""
    # Create PolicyAction with structured config
    policy = PolicyAction(
        action_type=PolicyActionType.RATE_LIMITING,
        config=RateLimitConfig(requests_per_minute=1000)
    )
    
    # Verify it was created successfully
    assert policy.config is not None
    assert isinstance(policy.config, RateLimitConfig)


def test_none_config_works():
    """Test that None config works without errors."""
    # Create PolicyAction with no config
    policy = PolicyAction(
        action_type=PolicyActionType.RATE_LIMITING,
        config=None
    )
    
    # Verify it was created successfully
    assert policy.config is None


def test_validation_error_message_content():
    """Test that validation error contains helpful information."""
    with pytest.raises(ValidationError) as exc_info:
        policy = PolicyAction(
            action_type=PolicyActionType.AUTHENTICATION,
            config={"auth_type": "oauth2"}
        )
    
    error_message = str(exc_info.value)
    
    # Check for key information in error message
    assert "dict-based config is no longer supported" in error_message.lower()
    assert "structured config" in error_message.lower()
    assert "migration guide" in error_message.lower()
    assert "vendor-neutral-policy-configuration-analysis.md" in error_message


def test_structured_config_with_correct_type():
    """Test that structured config with correct type works."""
    # Rate limiting with RateLimitConfig
    policy = PolicyAction(
        action_type=PolicyActionType.RATE_LIMITING,
        config=RateLimitConfig(requests_per_minute=1000)
    )
    assert policy.config is not None
    assert isinstance(policy.config, RateLimitConfig)
    assert policy.config.requests_per_minute == 1000


def test_structured_config_with_wrong_type():
    """Test that structured config with wrong type raises error."""
    with pytest.raises(ValidationError) as exc_info:
        # Try to use AuthenticationConfig for RATE_LIMITING action
        policy = PolicyAction(
            action_type=PolicyActionType.RATE_LIMITING,
            config=AuthenticationConfig(auth_type="oauth2")
        )
    
    error_message = str(exc_info.value)
    assert "does not match" in error_message.lower()
    assert "RateLimitConfig" in error_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
