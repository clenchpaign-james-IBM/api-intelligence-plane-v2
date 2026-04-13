# WebMethods API Gateway REST API Endpoints Summary

## Overview
This document summarizes the WebMethods API Gateway REST API endpoints based on the provided request/response samples.

## API Endpoints

### 1. GET /rest/apigateway/apis
**Purpose**: List all APIs registered in the gateway

**Response Structure** (`research/A04-apis-response.json`):
```json
{
  "apiResponse": [
    {
      "api": {
        "apiName": "string",
        "apiVersion": "string",
        "apiDescription": "string",
        "isActive": boolean,
        "type": "REST",
        "tracingEnabled": boolean,
        "publishedPortals": [],
        "systemVersion": integer,
        "id": "uuid"
      },
      "responseStatus": "SUCCESS"
    }
  ]
}
```

**Key Fields**:
- `apiName`: Name of the API
- `apiVersion`: Version string
- `id`: Unique identifier (UUID)
- `isActive`: Whether API is active
- `type`: API type (REST, SOAP, etc.)

---

### 2. GET /rest/apigateway/apis/{api_id}
**Purpose**: Get detailed information about a specific API

**Response Structure** (`research/A03-api-response.json`):
```json
{
  "apiResponse": {
    "api": {
      "apiDefinition": {
        "info": { /* OpenAPI info object */ },
        "basePath": "string",
        "tags": [],
        "schemes": [],
        "security": [],
        "paths": { /* OpenAPI paths object */ },
        "securityDefinitions": {},
        "definitions": {},
        "components": {
          "schemas": {},
          "requestBodies": {},
          "securitySchemes": {}
        },
        "type": "rest"
      },
      "nativeEndpoint": [
        {
          "passSecurityHeaders": boolean,
          "uri": "string",
          "connectionTimeoutDuration": integer,
          "alias": boolean
        }
      ],
      "apiName": "string",
      "apiVersion": "string",
      "apiDescription": "string",
      "maturityState": "string",
      "isActive": boolean,
      "type": "REST",
      "owner": "string",
      "policies": ["policy_id"],
      "tracingEnabled": boolean,
      "scopes": [],
      "publishedPortals": [],
      "creationDate": "string",
      "lastModified": "string",
      "systemVersion": integer,
      "gatewayEndpoints": {},
      "deployments": ["string"],
      "id": "uuid"
    },
    "responseStatus": "SUCCESS",
    "gatewayEndPoints": ["string"],
    "gatewayEndPointList": [
      {
        "endpointName": "string",
        "endpointDisplayName": "string",
        "endpoint": "string",
        "endpointType": "string",
        "endpointUrls": ["string"]
      }
    ],
    "versions": [
      {
        "versionNumber": "string",
        "apiId": "uuid"
      }
    ]
  }
}
```

**Key Fields**:
- `apiDefinition`: Complete OpenAPI/Swagger specification
- `nativeEndpoint`: Backend service endpoints
- `policies`: Array of policy IDs attached to this API
- `gatewayEndPointList`: Gateway endpoints where API is exposed
- `maturityState`: API maturity (Beta, Production, etc.)
- `owner`: API owner

---

### 3. GET /rest/apigateway/policies/{policy_id}
**Purpose**: Get policy configuration

**Response Structure** (`research/A05-policy-response.json`):
```json
{
  "policy": {
    "id": "uuid",
    "names": [
      {
        "value": "string",
        "locale": "string"
      }
    ],
    "descriptions": [
      {
        "value": "string",
        "locale": "string"
      }
    ],
    "scope": {
      "scopeConditions": []
    },
    "policyEnforcements": [
      {
        "enforcements": [
          {
            "enforcementObjectId": "uuid",
            "order": "string"
          }
        ],
        "stageKey": "string"
      }
    ],
    "policyScope": "SERVICE",
    "global": boolean,
    "active": boolean,
    "systemPolicy": boolean
  }
}
```

**Policy Stages**:
- `transport`: Transport-level policies (TLS, HTTP)
- `requestPayloadProcessing`: Request validation, transformation
- `IAM`: Identity and Access Management
- `LMT`: Limit (rate limiting, throttling)
- `routing`: Routing policies
- `responseProcessing`: Response transformation

**Key Fields**:
- `policyEnforcements`: Array of policy stages with enforcement objects
- `enforcementObjectId`: References a PolicyAction
- `stageKey`: Pipeline stage where policy is applied
- `order`: Execution order within stage

---

### 4. PUT /rest/apigateway/policies/{policy_id}
**Purpose**: Update policy configuration

**Request Structure** (`research/A05-policy-request.json`):
```json
{
  "policy": {
    "id": "uuid",
    "names": [
      {
        "value": "string",
        "locale": "string"
      }
    ],
    "descriptions": [
      {
        "value": "string",
        "locale": "string"
      }
    ],
    "policyEnforcements": [
      {
        "enforcements": [
          {
            "enforcementObjectId": "uuid"
          }
        ],
        "stageKey": "string"
      }
    ],
    "policyScope": "SERVICE",
    "global": boolean,
    "active": boolean,
    "systemPolicy": boolean
  }
}
```

**Notes**:
- Request omits `scope` field (read-only)
- Request omits `order` field in enforcements (auto-assigned)
- Can add/remove enforcement objects by modifying `policyEnforcements` array

---

### 5. GET /rest/apigateway/policyActions/{policyaction_id}
**Purpose**: Get policy action (enforcement object) configuration

**Response Structure** (`research/A06-policyaction-response.json`):
```json
{
  "policyAction": {
    "id": "uuid",
    "names": [
      {
        "value": "string",
        "locale": "string"
      }
    ],
    "templateKey": "string",
    "parameters": [
      {
        "templateKey": "string",
        "values": ["string"]
      }
    ],
    "active": boolean
  }
}
```

**Example Template Keys**:
- `validateAPISpec`: API specification validation
- `requireHTTPS`: Enforce HTTPS
- `rateLimiting`: Rate limiting configuration
- `authentication`: Authentication policies
- `authorization`: Authorization policies

**Key Fields**:
- `templateKey`: Type of policy action
- `parameters`: Configuration parameters for the action
- Each parameter has `templateKey` and `values` array

---

### 6. POST /rest/apigateway/policyActions
**Purpose**: Create new policy action

**Request Structure** (`research/A06-policyaction-request.json`):
```json
{
  "policyAction": {
    "id": "uuid",
    "names": [
      {
        "value": "string",
        "locale": "string"
      }
    ],
    "templateKey": "string",
    "parameters": [
      {
        "templateKey": "string",
        "values": ["string"]
      }
    ],
    "active": boolean
  }
}
```

**Notes**:
- Same structure as GET response
- `id` can be provided or auto-generated
- After creation, policy action must be attached to a policy via PUT /policies/{policy_id}

---

### 7. GET TransactionalLog (OpenSearch Query)
**Purpose**: Query transactional event logs

**Query Method**: OpenSearch search query with filter
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "eventType": "Transactional"
          }
        }
      ]
    }
  }
}
```

**Expected Fields** (based on WebMethods TransactionalLog model):
- `eventType`: "Transactional"
- `timestamp`: Event timestamp
- `apiId`: API identifier
- `apiName`: API name
- `apiVersion`: API version
- `totalTime`: Total request time (ms)
- `providerTime`: Backend service time (ms)
- `gatewayTime`: Gateway processing time (ms)
- `httpMethod`: HTTP method
- `requestPath`: Request path
- `statusCode`: HTTP status code
- `applicationId`: Client application ID
- `applicationName`: Client application name
- `errorOrigin`: Error source (NATIVE, GATEWAY)
- `errorMessage`: Error details
- `cacheHit`: Cache hit flag
- `externalCalls`: Array of external service calls

---

## Integration Architecture

### Data Flow
1. **API Discovery**: GET /apis → Transform to vendor-neutral API model
2. **API Details**: GET /apis/{id} → Extract OpenAPI spec, policies, endpoints
3. **Policy Management**: GET/PUT /policies/{id} → Security/optimization policies
4. **Policy Actions**: GET/POST /policyActions → Individual policy configurations
5. **Analytics**: OpenSearch query → Transactional logs for metrics aggregation

### Transformation Requirements
- **API Model**: WebMethods API → Vendor-neutral `api.py:API`
- **Policy Model**: WebMethods Policy → Vendor-neutral `PolicyAction` with `vendor_config`
- **Metrics**: TransactionalLog → Time-bucketed `metric.py:Metric`
- **Logs**: TransactionalLog → Vendor-neutral `transaction.py:TransactionalLog`

### Adapter Responsibilities (WebMethodsGatewayAdapter)
1. Transform WebMethods API response to vendor-neutral API model
2. Transform WebMethods Policy/PolicyAction to vendor-neutral PolicyAction
3. Collect transactional logs from OpenSearch
4. Transform transactional logs to vendor-neutral TransactionalLog model
5. Apply security/optimization policies via PUT /policies and POST /policyActions
6. Handle WebMethods-specific fields in `vendor_metadata`

---

## Key Observations

1. **Comprehensive OpenAPI Support**: Full OpenAPI 3.0 specification in `apiDefinition`
2. **Policy Pipeline**: Multi-stage policy enforcement (transport → IAM → routing → etc.)
3. **Policy Actions**: Reusable policy action templates with parameters
4. **Gateway Endpoints**: Multiple endpoint types (DEFAULT, CUSTOM, etc.)
5. **Version Management**: API versioning with version history
6. **Transactional Logs**: Rich event data for analytics and metrics
7. **Localization**: Multi-locale support for names and descriptions

---

## Implementation Notes

### Phase 1: Discovery & Monitoring
- Use GET /apis for initial discovery
- Use GET /apis/{id} for detailed API information
- Store in vendor-neutral format with `vendor_metadata`

### Phase 2: Policy Management
- Use GET /policies/{id} to read existing policies
- Use GET /policyActions/{id} to read policy actions
- Use POST /policyActions to create new actions
- Use PUT /policies/{id} to attach actions to policies

### Phase 3: Analytics Integration
- Query OpenSearch for transactional logs (eventType: "Transactional")
- Transform to vendor-neutral TransactionalLog model
- Aggregate into time-bucketed metrics
- Support drill-down from metrics to raw logs

### Phase 4: Remediation
- Create policy actions for security/optimization
- Attach to API policies
- Verify through re-scanning