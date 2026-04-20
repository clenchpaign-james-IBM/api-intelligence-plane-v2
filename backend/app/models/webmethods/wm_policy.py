"""
Python Pydantic models for API Gateway Policy and PolicyAction.
Converted from Java classes.
IBM Confidential - Copyright 2024 IBM Corp.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class InternationalizedString(BaseModel):
    """
    Model to store a string with its corresponding locale.
    Used for multi-language support.
    """
    value: Optional[str] = None
    locale: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class ExtendedProperties(BaseModel):
    """Extended properties as key-value pairs."""
    key: Optional[str] = None
    value: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class PolicyActionParameter(BaseModel):
    """
    Represents values needed for a policy action to execute.
    Can be primitive type or complex structure referring to another PolicyActionParameter.
    """
    template_key: Optional[str] = Field(None, alias="templateKey")
    values: Optional[List[str]] = None
    parameters: Optional[List['PolicyActionParameter']] = None
    extended_properties: Optional[List[ExtendedProperties]] = Field(None, alias="extendedProperties")
    
    model_config = ConfigDict(populate_by_name=True)


class Enforcement(BaseModel):
    """
    Model contains a policy enforcement id and its order.
    """
    enforcement_object_id: Optional[str] = Field(None, alias="enforcementObjectId")
    order: Optional[str] = None
    parent_policy_id: Optional[str] = Field(None, alias="parentPolicyId")
    
    model_config = ConfigDict(populate_by_name=True)


class PolicyEnforcements(BaseModel):
    """
    Contains the list of policy action ids specific to a stage.
    """
    enforcements: Optional[List[Enforcement]] = Field(default_factory=list)
    stage_key: Optional[str] = Field(None, alias="stageKey", description="Policy stage key")
    
    model_config = ConfigDict(populate_by_name=True)


class LogicalOperator(str, Enum):
    """Logical operator for scope conditions."""
    AND = "AND"
    OR = "OR"


class ScopeConditionType(str, Enum):
    """Filter type for scope conditions."""
    APIS = "apis"
    HTTP_METHOD = "httpMethod"
    TAGS = "tags"


class Attribute(BaseModel):
    """Attribute for scope condition filtering."""
    key: Optional[str] = None
    value: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScopeCondition(BaseModel):
    """
    Scope condition with attributes for filtering APIs, resources, or operations.
    """
    filter_type: Optional[ScopeConditionType] = Field(None, alias="filterType")
    attributes: Optional[List[Attribute]] = None
    logical_connector: LogicalOperator = Field(LogicalOperator.AND, alias="logicalConnector")
    
    model_config = ConfigDict(populate_by_name=True)


class ServiceType(str, Enum):
    """API service types."""
    REST = "rest"
    SOAP = "soap"
    WEBSOCKET = "websocket"
    GRAPHQL = "graphql"
    ODATA = "odata"


class Scope(BaseModel):
    """
    Defines filtering criteria for Global policy.
    Specifies APIs, resources, or operations where policy enforcements apply.
    """
    applicable_api_types: Optional[List[ServiceType]] = Field(None, alias="applicableAPITypes")
    scope_conditions: Optional[List[ScopeCondition]] = Field(None, alias="scopeConditions")
    logical_connector: Optional[LogicalOperator] = Field(None, alias="logicalConnector")
    
    model_config = ConfigDict(populate_by_name=True)


class PolicyScope(str, Enum):
    """
    Policy scope enumeration.
    Defines the level at which a policy can be applied.
    """
    GLOBAL = "GLOBAL"
    METHOD = "METHOD"
    OPERATION = "OPERATION"
    RESOURCE = "RESOURCE"
    SERVICE = "SERVICE"
    PACKAGE = "PACKAGE"
    TEMPLATE = "TEMPLATE"
    SCOPE = "SCOPE"


class Policy(BaseModel):
    """
    A policy is a group of policy (runtime) enforcements.
    Contains list of policy enforcement ids organized by stages.
    Can be Service/scope/package/global/template policy.
    """
    # Core identification
    id: str = Field("", description="Policy ID")
    doc_type: str = Field("policy", alias="_docType")
    
    # Names and descriptions with locale support
    names: Optional[List[InternationalizedString]] = Field(
        None, 
        description="List of names for the policy with corresponding locale information"
    )
    descriptions: Optional[List[InternationalizedString]] = Field(
        None,
        description="List of descriptions for the policy with corresponding locale information"
    )
    
    # Parameters and scope
    parameters: Optional[List[PolicyActionParameter]] = Field(
        None,
        description="Basic details of threat protection rule (name, description, action, error message, etc.)"
    )
    scope: Optional[Scope] = Field(
        None,
        description="Scope for GLOBAL policy (only applicable for GLOBAL Policy)"
    )
    
    # Policy enforcements
    policy_enforcements: Optional[List[PolicyEnforcements]] = Field(
        None,
        alias="policyEnforcements",
        description="List of policy enforcement ids grouped by stages"
    )
    
    # Policy properties
    is_global: bool = Field(False, alias="global", description="True for global or threat protection policy")
    policy_scope: Optional[PolicyScope] = Field(None, alias="policyScope", description="Scope of the policy")
    is_active: bool = Field(False, alias="active", description="True if policy is active")
    is_system_policy: bool = Field(
        False,
        alias="systemPolicy",
        description="True if global policy is system level (created by default)"
    )
    
    @field_validator('policy_scope', mode='before')
    @classmethod
    def normalize_policy_scope(cls, v):
        """Convert policy scope values to uppercase for enum compatibility."""
        if isinstance(v, str):
            return v.upper()
        return v
    
    model_config = ConfigDict(populate_by_name=True)


class PolicyAction(BaseModel):
    """
    Policy action containing details about a policy action in API Gateway.
    Represents a specific enforcement action that can be applied.
    """
    # Core identification
    id: str = Field("", description="Policy Action ID")
    doc_type: str = Field("policyActions", alias="_docType")
    
    # Names and descriptions with locale support
    names: Optional[List[InternationalizedString]] = Field(
        None,
        description="List of policy action names with corresponding locale information"
    )
    descriptions: Optional[List[InternationalizedString]] = Field(
        None,
        description="List of policy action descriptions with corresponding locale information"
    )
    
    # Template and parameters
    template_key: Optional[str] = Field(None, alias="templateKey", description="Template key of the policy action")
    parameters: Optional[List[PolicyActionParameter]] = Field(
        None,
        description="List of values configured for this policy action"
    )
    
    # Stage information
    stage_key: Optional[str] = Field(None, alias="stageKey", description="Stage key when created from a policy")
    
    model_config = ConfigDict(populate_by_name=True)


# Constants for policy action types
class PolicyActionConstants:
    """Constants for policy action template keys and enable flags."""
    
    # Template keys
    MSG_SIZE_FILTER = "msgsizelimitfilter"
    JSON_THREAT_PROTECTION_FILTER = "jsonthreatprotectionfilter"
    XML_THREAT_PROTECTION_FILTER = "xmlthreatprotectionfilter"
    SQL_INJECTION_FILTER = "sqlinjectionfilter"
    MOBILE_APP_PROTECTION_FILTER = "mobileappprotectionfilter"
    ANTI_VIRUS_FILTER = "antivirusfilter"
    CUSTOM_FILTER = "customfilter"
    OAUTH_FILTER = "oauthfilter"
    IP_DOS = "ipdos"
    GLOBAL_IP_DOS = "globalipdos"
    
    # Enable flags
    IS_ENABLED = "isEnabled"
    IS_JSON_THREAT_PROTECTION_ENABLED = "isJSONThreatProtectionEnabled"
    IS_XML_THREAT_PROTECTION_ENABLED = "isXMLThreatProtectionEnabled"
    IS_MESSAGE_SIZE_ENABLED = "isMessageSizeEnabled"
    IS_MOBILE_APP_PROTECTION_ENABLED = "isMobileAppProtectionEnabled"
    IS_SQL_INJECTION_FILTER_ENABLED = "isSQLInjectionFilterEnabled"
    IS_ANTI_VIRUS_SCAN_ENABLED = "isAntiVirusScanEnabled"
    IS_CUSTOM_FILTER_ENABLED = "isCustomFilterEnabled"
    IS_OAUTH_ENABLED = "isOAuthEnabled"
    IS_DOS_ENABLED = "isDOSEnabled"
    
    # Values
    TRUE = "true"
    FALSE = "false"
    
    # Mapping of template keys to enable flags
    TEMPLATE_KEY_ENABLE_MAP = {
        MSG_SIZE_FILTER: IS_MESSAGE_SIZE_ENABLED,
        MOBILE_APP_PROTECTION_FILTER: IS_MOBILE_APP_PROTECTION_ENABLED,
        SQL_INJECTION_FILTER: IS_SQL_INJECTION_FILTER_ENABLED,
        ANTI_VIRUS_FILTER: IS_ANTI_VIRUS_SCAN_ENABLED,
        CUSTOM_FILTER: IS_CUSTOM_FILTER_ENABLED,
        OAUTH_FILTER: IS_OAUTH_ENABLED,
        JSON_THREAT_PROTECTION_FILTER: IS_JSON_THREAT_PROTECTION_ENABLED,
        XML_THREAT_PROTECTION_FILTER: IS_XML_THREAT_PROTECTION_ENABLED,
        IP_DOS: IS_DOS_ENABLED,
        GLOBAL_IP_DOS: IS_DOS_ENABLED,
    }


class PolicyConstants:
    """Constants for policy operations."""
    
    POLICY_ID = "policy"
    SORT_FIELD = "names.value"
    THREAT_PROTECTION_STAGE_KEY = "threatProtection"
    IS_RULE_ENABLED = "isRuleEnabled"
    TRUE = "true"

# Made with Bob
