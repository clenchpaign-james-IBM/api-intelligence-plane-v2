"""
Helper utilities for policy configuration management.

Provides backward compatibility helpers for converting between dict-based
and structured policy configurations during the migration period.
"""

from typing import Any, Optional, Type, TypeVar, Union
import warnings

from .policy_configs import (
    RateLimitConfig,
    AuthenticationConfig,
    AuthorizationConfig,
    CachingConfig,
    CorsConfig,
    ValidationConfig,
    DataMaskingConfig,
    TransformationConfig,
    LoggingConfig,
    TlsConfig,
    CompressionConfig,
    PolicyConfigType,
)
from .api import PolicyActionType

T = TypeVar('T', bound=PolicyConfigType)


# ============================================================================
# Type Mapping
# ============================================================================

POLICY_CONFIG_TYPE_MAP: dict[PolicyActionType, Type[PolicyConfigType]] = {
    PolicyActionType.RATE_LIMITING: RateLimitConfig,
    PolicyActionType.AUTHENTICATION: AuthenticationConfig,
    PolicyActionType.AUTHORIZATION: AuthorizationConfig,
    PolicyActionType.CACHING: CachingConfig,
    PolicyActionType.CORS: CorsConfig,
    PolicyActionType.VALIDATION: ValidationConfig,
    PolicyActionType.DATA_MASKING: DataMaskingConfig,
    PolicyActionType.TRANSFORMATION: TransformationConfig,
    PolicyActionType.LOGGING: LoggingConfig,
    PolicyActionType.TLS: TlsConfig,
    PolicyActionType.COMPRESSION: CompressionConfig,
}


# ============================================================================
# Conversion Functions
# ============================================================================

def dict_to_structured_config(
    config_dict: dict[str, Any],
    action_type: PolicyActionType
) -> Optional[PolicyConfigType]:
    """
    Convert a dict-based config to structured config.
    
    Args:
        config_dict: Dictionary configuration
        action_type: Type of policy action
        
    Returns:
        Structured config object or None if conversion fails
        
    Example:
        >>> config_dict = {"requests_per_minute": 1000, "burst_allowance": 100}
        >>> structured = dict_to_structured_config(config_dict, PolicyActionType.RATE_LIMITING)
        >>> isinstance(structured, RateLimitConfig)
        True
    """
    config_class = POLICY_CONFIG_TYPE_MAP.get(action_type)
    if not config_class:
        warnings.warn(
            f"No structured config class found for action_type: {action_type}",
            UserWarning
        )
        return None
    
    try:
        return config_class(**config_dict)
    except Exception as e:
        warnings.warn(
            f"Failed to convert dict to {config_class.__name__}: {e}",
            UserWarning
        )
        return None


def structured_to_dict_config(config: PolicyConfigType) -> dict[str, Any]:
    """
    Convert a structured config to dict.
    
    Args:
        config: Structured configuration object
        
    Returns:
        Dictionary representation of the config
        
    Example:
        >>> config = RateLimitConfig(requests_per_minute=1000)
        >>> config_dict = structured_to_dict_config(config)
        >>> config_dict["requests_per_minute"]
        1000
    """
    return config.model_dump(exclude_none=True)


def normalize_policy_config(
    config: Union[PolicyConfigType, dict[str, Any], None],
    action_type: PolicyActionType,
    prefer_structured: bool = True
) -> Union[PolicyConfigType, dict[str, Any], None]:
    """
    Normalize policy config to preferred format.
    
    Args:
        config: Policy configuration (structured or dict)
        action_type: Type of policy action
        prefer_structured: If True, convert dicts to structured configs
        
    Returns:
        Normalized configuration in preferred format
        
    Example:
        >>> config_dict = {"requests_per_minute": 1000}
        >>> normalized = normalize_policy_config(config_dict, PolicyActionType.RATE_LIMITING)
        >>> isinstance(normalized, RateLimitConfig)
        True
    """
    if config is None:
        return None
    
    # Already in preferred format
    if prefer_structured and not isinstance(config, dict):
        return config
    if not prefer_structured and isinstance(config, dict):
        return config
    
    # Convert to preferred format
    if prefer_structured and isinstance(config, dict):
        return dict_to_structured_config(config, action_type)
    elif not isinstance(config, dict):
        # Convert structured to dict
        return structured_to_dict_config(config)
    else:
        return config


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_policy_config(
    config: Union[PolicyConfigType, dict[str, Any]],
    action_type: PolicyActionType
) -> tuple[bool, Optional[str]]:
    """
    Validate policy configuration.
    
    Args:
        config: Policy configuration to validate
        action_type: Expected policy action type
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> config = RateLimitConfig(requests_per_minute=1000)
        >>> is_valid, error = validate_policy_config(config, PolicyActionType.RATE_LIMITING)
        >>> is_valid
        True
    """
    # If it's a dict, try to convert to structured config for validation
    if isinstance(config, dict):
        structured = dict_to_structured_config(config, action_type)
        if structured is None:
            return False, "Failed to convert dict to structured config"
        config = structured
    
    # Check type matches action_type
    expected_type = POLICY_CONFIG_TYPE_MAP.get(action_type)
    if expected_type and not isinstance(config, expected_type):
        return False, f"Config type {type(config).__name__} does not match action_type {action_type}"
    
    return True, None


def get_config_schema(action_type: PolicyActionType) -> Optional[dict[str, Any]]:
    """
    Get JSON schema for a policy action type.
    
    Args:
        action_type: Policy action type
        
    Returns:
        JSON schema dict or None if not found
        
    Example:
        >>> schema = get_config_schema(PolicyActionType.RATE_LIMITING)
        >>> "properties" in schema
        True
    """
    config_class = POLICY_CONFIG_TYPE_MAP.get(action_type)
    if not config_class:
        return None
    
    return config_class.model_json_schema()


# ============================================================================
# Migration Helpers
# ============================================================================

def migrate_dict_configs_to_structured(
    policy_actions: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Migrate a list of policy actions from dict configs to structured configs.
    
    Args:
        policy_actions: List of policy action dicts
        
    Returns:
        List of policy actions with structured configs where possible
        
    Example:
        >>> actions = [
        ...     {
        ...         "action_type": "rate_limiting",
        ...         "config": {"requests_per_minute": 1000}
        ...     }
        ... ]
        >>> migrated = migrate_dict_configs_to_structured(actions)
        >>> isinstance(migrated[0]["config"], RateLimitConfig)
        True
    """
    migrated = []
    
    for action in policy_actions:
        action_copy = action.copy()
        config = action_copy.get("config")
        action_type_str = action_copy.get("action_type")
        
        if config and isinstance(config, dict) and action_type_str:
            try:
                # Convert string to enum
                action_type = PolicyActionType(action_type_str)
                structured = dict_to_structured_config(config, action_type)
                if structured:
                    action_copy["config"] = structured
            except (ValueError, KeyError):
                # Keep original if conversion fails
                pass
        
        migrated.append(action_copy)
    
    return migrated


def get_migration_report(
    policy_actions: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Generate a report on policy config migration status.
    
    Args:
        policy_actions: List of policy action dicts
        
    Returns:
        Report dict with migration statistics
        
    Example:
        >>> actions = [{"action_type": "rate_limiting", "config": {...}}]
        >>> report = get_migration_report(actions)
        >>> report["total_policies"]
        1
    """
    total = len(policy_actions)
    dict_configs = 0
    structured_configs = 0
    no_config = 0
    migration_possible = 0
    
    for action in policy_actions:
        config = action.get("config")
        
        if config is None:
            no_config += 1
        elif isinstance(config, dict):
            dict_configs += 1
            # Check if migration is possible
            action_type_str = action.get("action_type")
            if action_type_str:
                try:
                    action_type = PolicyActionType(action_type_str)
                    if dict_to_structured_config(config, action_type):
                        migration_possible += 1
                except (ValueError, KeyError):
                    pass
        else:
            structured_configs += 1
    
    return {
        "total_policies": total,
        "dict_configs": dict_configs,
        "structured_configs": structured_configs,
        "no_config": no_config,
        "migration_possible": migration_possible,
        "migration_percentage": (migration_possible / dict_configs * 100) if dict_configs > 0 else 0,
        "structured_percentage": (structured_configs / total * 100) if total > 0 else 0,
    }


# ============================================================================
# Deprecation Warnings
# ============================================================================

def warn_dict_config_deprecated(action_type: PolicyActionType) -> None:
    """
    Emit deprecation warning for dict-based configs.
    
    This will be used in Phase 4 of the migration.
    
    Args:
        action_type: Policy action type using dict config
    """
    warnings.warn(
        f"Dict-based config for {action_type} is deprecated. "
        f"Please use structured {POLICY_CONFIG_TYPE_MAP[action_type].__name__} instead. "
        "Dict configs will be removed in a future version.",
        DeprecationWarning,
        stacklevel=3
    )


# Export all helpers
__all__ = [
    "POLICY_CONFIG_TYPE_MAP",
    "dict_to_structured_config",
    "structured_to_dict_config",
    "normalize_policy_config",
    "validate_policy_config",
    "get_config_schema",
    "migrate_dict_configs_to_structured",
    "get_migration_report",
    "warn_dict_config_deprecated",
]

# Made with Bob
