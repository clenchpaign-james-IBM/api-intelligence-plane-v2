
# Security MCP Server Feature Analysis

**Date**: 2026-04-14  
**Scope**: Security MCP server feature review against product spec, implementation plan, MCP tool contract, and current backend/MCP implementation  
**Primary focus**: Vendor-neutral alignment and the requirement that the MCP server must delegate AI-driven insight generation to backend APIs rather than directly invoking OpenSearch

---

## Executive Assessment

The current Security MCP server is **directionally aligned** with the intended architecture, but it is **not yet perfect** and has several important architectural and implementation gaps.

### What is strong

- The Security MCP server is explicitly implemented as a thin wrapper over backend REST APIs, which matches the required architectural direction in [`SecurityMCPServer`](../mcp-servers/security_server.py:36).
- The MCP layer itself delegates scan, posture, remediation, vulnerability listing, and verification through [`BackendClient._request()`](../mcp-servers/common/backend_client.py:60) instead of directly querying OpenSearch.
- The backend security analysis logic is largely modeled around vendor-neutral API concepts such as [`API`](../backend/app/models/base/api.py), [`PolicyActionType`](../backend/app/models/base/api.py), and adapter-mediated remediation through [`BaseGatewayAdapter`](../backend/app/adapters/base.py:16).
- The security agent uses normalized API metadata and normalized metrics for analysis rather than vendor-native payloads in the MCP layer, which is the right separation of concerns for a vendor-neutral platform.

### Main concerns

- The Security MCP server still mixes **security scanning** with **compliance detection** in its public description and scan semantics, even though the spec and plan explicitly separate security and compliance into distinct features.
- The backend service and agent still contain direct OpenSearch access patterns in the security flow, which does not violate the user’s MCP rule directly, but weakens architectural consistency and backend abstraction quality.
- Automated remediation in [`SecurityService._apply_automated_remediation()`](../backend/app/services/security_service.py:399) passes plain dictionaries to adapter methods whose abstract interface expects vendor-neutral [`PolicyAction`](../backend/app/models/base/api.py:157) objects. That is a significant vendor-neutrality gap.
- There are contract and runtime inconsistencies, including incorrect port documentation/usage, capability framing, and response model mismatches.
- Some AI prompts and tool descriptions still reflect older mixed security/compliance assumptions.

### Overall verdict

**Backend delegation compliance in MCP layer**: Strong  
**No direct OpenSearch usage in Security MCP server**: Strong  
**Vendor-neutral design alignment**: Moderate  
**Security/compliance boundary clarity**: Weak  
**Adapter-mediated remediation quality**: Moderate to weak  
**Contract/implementation consistency**: Moderate

---

## Review Basis

This analysis was based on the following sources:

- [`spec.md`](../specs/001-api-intelligence-plane/spec.md)
- [`plan.md`](../specs/001-api-intelligence-plane/plan.md)
- [`tasks.md`](../specs/001-api-intelligence-plane/tasks.md)
- [`mcp-tools.md`](../specs/001-api-intelligence-plane/contracts/mcp-tools.md)
- [`security_server.py`](../mcp-servers/security_server.py)
- [`backend_client.py`](../mcp-servers/common/backend_client.py)
- [`security.py`](../backend/app/api/v1/security.py)
- [`security_service.py`](../backend/app/services/security_service.py)
- [`security_agent.py`](../backend/app/agents/security_agent.py)
- [`deps.py`](../backend/app/api/deps.py)
- [`factory.py`](../backend/app/adapters/factory.py)
- [`base.py`](../backend/app/adapters/base.py)
- [`opensearch.py`](../mcp-servers/common/opensearch.py)

---

## 1. Alignment with the Required MCP Delegation Pattern

### 1.1 Status: Aligned

The explicit user note says the MCP server should delegate calls to backend APIs to get AI-driven insights and should not directly invoke OpenSearch.

That requirement is met by the Security MCP server implementation:

- [`SecurityMCPServer.__init__()`](../mcp-servers/security_server.py:52) initializes [`BackendClient`](../mcp-servers/common/backend_client.py:18).
- The server’s tools call backend endpoints through [`BackendClient._request()`](../mcp-servers/common/backend_client.py:60), including:
  - scan via [`scan_api_security()`](../mcp-servers/security_server.py:123)
  - remediation via [`remediate_vulnerability()`](../mcp-servers/security_server.py:192)
  - posture via [`get_security_posture()`](../mcp-servers/security_server.py:254)
  - vulnerability listing via [`list_vulnerabilities()`](../mcp-servers/security_server.py:318)
  - verification via [`verify_remediation()`](../mcp-servers/security_server.py:388)

The MCP layer itself does not use [`MCPOpenSearchClient`](../mcp-servers/common/opensearch.py:16), which is the right outcome.

### 1.2 Strength

This is the strongest part of the feature. It delivers:

- backend code reuse
- single place for AI orchestration and business logic
- cleaner MCP tool surface
- better future portability across gateway vendors
- simpler enforcement of vendor-neutral backend contracts

### 1.3 Important nuance

Even though the MCP layer is compliant, the backend internals are not consistently abstraction-driven. Both [`SecurityService.scan_all_apis()`](../backend/app/services/security_service.py:142) and [`SecurityAgent._fetch_recent_metrics()`](../backend/app/agents/security_agent.py:265) directly query repository OpenSearch clients. That does not violate the MCP rule, but it weakens the broader “delegate and centralize through service/repository abstractions” architecture.

---

## 2. Alignment with the Security Feature in Spec and Plan

### 2.1 Status: Partially aligned

The security feature in the spec is clearly defined as:

- hybrid analysis
- multi-source analysis using API metadata, real-time metrics, and traffic patterns
- real remediation through gateway adapters
- focus on active vulnerabilities and immediate threat response

This is captured in [`spec.md`](../specs/001-api-intelligence-plane/spec.md:144) and reinforced in [`plan.md`](../specs/001-api-intelligence-plane/plan.md:30).

The current implementation does reflect several of these goals:

- hybrid analysis in [`SecurityAgent.analyze_api_security()`](../backend/app/agents/security_agent.py:124)
- traffic-pattern-aware checks in methods like [`_check_rate_limiting()`](../backend/app/agents/security_agent.py:494)
- adapter-based remediation flow via [`GatewayAdapterFactory.create_adapter()`](../backend/app/adapters/factory.py:34)
- policy-oriented gateway remediation logic in [`SecurityService._apply_automated_remediation()`](../backend/app/services/security_service.py:399)

### 2.2 Strong alignment points

#### A. Hybrid analysis is real, not just documented

The backend agent genuinely combines rule-based checks with AI-supported reasoning:

- deterministic checks for authentication, authorization, rate limiting, TLS, validation
- AI-assisted severity and contextual judgment in methods like:
  - [`_determine_severity_with_ai()`](../backend/app/agents/security_agent.py:724)
  - [`_check_authorization_need_with_ai()`](../backend/app/agents/security_agent.py:769)
  - [`_check_cors_with_ai()`](../backend/app/agents/security_agent.py:805)
  - [`_check_security_headers_with_ai()`](../backend/app/agents/security_agent.py:846)

That is well aligned with the hybrid security architecture from [`plan.md`](../specs/001-api-intelligence-plane/plan.md:30).

#### B. Multi-source analysis is materially implemented

The agent uses:

- normalized API metadata from [`API`](../backend/app/models/base/api.py)
- metrics from [`MetricsRepository`](../backend/app/db/repositories/metrics_repository.py)
- derived traffic analysis in [`_analyze_traffic_patterns()`](../backend/app/agents/security_agent.py:313)

This maps well to the “API metadata, real-time metrics, and traffic patterns” requirement in [`spec.md`](../specs/001-api-intelligence-plane/spec.md:146).

#### C. Remediation is intended to be adapter-mediated

The service does not attempt to modify a specific vendor directly in the MCP layer. Instead it goes through the adapter factory and gateway adapter interface:

- [`GatewayAdapterFactory.create_adapter()`](../backend/app/adapters/factory.py:34)
- adapter methods in [`BaseGatewayAdapter`](../backend/app/adapters/base.py:16)

This is the right direction for vendor-neutral policy application.

---

## 3. Vendor-Neutral Design Assessment

### 3.1 Status: Mixed

The security feature has a solid vendor-neutral foundation, but important implementation details are not fully aligned.

### 3.2 What is aligned

#### A. Security analysis operates on vendor-neutral API structure

The agent checks normalized fields such as:

- [`api.authentication_type`](../backend/app/agents/security_agent.py:381)
- [`api.policy_actions`](../backend/app/agents/security_agent.py:715)
- [`api.endpoints`](../backend/app/agents/security_agent.py:389)
- [`api.intelligence_metadata`](../backend/app/agents/security_agent.py:390)

