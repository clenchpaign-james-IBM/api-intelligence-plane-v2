# Security remediation plan analysis

## Scope

This note analyzes how the security remediation plan is generated, returned, propagated, and persisted across the backend, API layer, MCP layer, and frontend.

Primary focus areas:

- [`backend/app/agents/security_agent.py`](backend/app/agents/security_agent.py)
- [`backend/app/services/security_service.py`](backend/app/services/security_service.py)
- [`backend/app/api/v1/security.py`](backend/app/api/v1/security.py)
- [`backend/app/db/repositories/vulnerability_repository.py`](backend/app/db/repositories/vulnerability_repository.py)
- [`backend/app/models/vulnerability.py`](backend/app/models/vulnerability.py)
- [`frontend/src/services/security.ts`](frontend/src/services/security.ts)
- [`frontend/src/components/query/QueryResponse.tsx`](frontend/src/components/query/QueryResponse.tsx)
- [`mcp-servers/security_server.py`](mcp-servers/security_server.py)

## Key observation 1: the agent currently collapses multiple plans into one

In [`SecurityAgent._create_remediation_plan()`](backend/app/agents/security_agent.py:1026), the LLM response parser supports the possibility that the model returns multiple JSON objects. However, when multiple objects are successfully parsed, the method sorts them by priority and returns only the first object in [`security_agent.py`](backend/app/agents/security_agent.py:1147).

That means the current behavior is:

- multiple candidate plans may be produced by the LLM
- multiple candidate plans may even be parsed successfully
- but only one plan survives the method boundary
- all other parsed plans are discarded immediately

### Why this matters

This is not just a formatting choice. It creates ambiguity about the intended contract of [`remediation_plan`](backend/app/agents/security_agent.py:54):

- If the plan is supposed to be a **single consolidated remediation plan**, then parsing multiple JSON objects is a fallback mechanism and the code should probably merge them into one normalized structure.
- If the plan is supposed to be **a set of prioritized plans or per-vulnerability/per-theme recommendations**, then returning only the first object is lossy and semantically incorrect.

Right now the implementation does neither cleanly. It accepts multiple plans, but silently drops all except one.

## Key observation 2: the data contract says “single dict”, not “list of plans”

The in-memory workflow state defines [`remediation_plan`](backend/app/agents/security_agent.py:54) as a `Dict[str, Any]` in [`SecurityAnalysisState`](backend/app/agents/security_agent.py:46).

The direct analysis path returns a single dict in [`_analyze_direct()`](backend/app/agents/security_agent.py:177), and the workflow path also writes a single dict in [`_generate_remediation_plan_node()`](backend/app/agents/security_agent.py:254).

The REST response model also encodes this assumption:

- [`ScanResponse.remediation_plan`](backend/app/api/v1/security.py:40) is declared as `dict`
- frontend [`ScanResponse.remediation_plan`](frontend/src/types/index.ts:536) is declared as `Record<string, any>`

So structurally the rest of the system expects exactly one object, not an array.

### Conclusion

Returning all parsed objects directly would currently be a breaking contract change across:

- [`SecurityAnalysisState`](backend/app/agents/security_agent.py:46)
- [`ScanResponse`](backend/app/api/v1/security.py:30)
- frontend [`ScanResponse`](frontend/src/types/index.ts:528)
- any code assuming object-style access to a single plan

## Key observation 3: the remediation plan is propagated, but not persisted

The plan is generated and returned through several layers:

1. created in [`SecurityAgent._create_remediation_plan()`](backend/app/agents/security_agent.py:1026)
2. attached to analysis results in [`SecurityAgent.analyze_api_security()`](backend/app/agents/security_agent.py:156) and [`SecurityAgent._analyze_direct()`](backend/app/agents/security_agent.py:195)
3. returned by [`SecurityService.scan_api_security()`](backend/app/services/security_service.py:91)
4. exposed by [`ScanResponse`](backend/app/api/v1/security.py:30)
5. documented by MCP [`scan_api_security()`](mcp-servers/security_server.py:123)

However, during persistence only vulnerabilities are stored. In [`SecurityService.scan_api_security()`](backend/app/services/security_service.py:120), each vulnerability is written via [`vulnerability_repository.create()`](backend/app/services/security_service.py:130), but the remediation plan is only copied into the returned payload at [`security_service.py`](backend/app/services/security_service.py:149). There is no repository call that stores the plan itself.

### Net result

The remediation plan is:

- generated
- returned to callers
- available transiently in API/MCP responses

But it is not:

- stored in OpenSearch as its own entity
- attached to the persisted vulnerability documents
- versioned
- queryable later
- available for historical/security trend analysis after the response is gone

So the user’s concern is correct: today the remediation plan appears to be mostly an ephemeral response artifact.

## Key observation 4: remediation is connected to vulnerabilities operationally, but not by data model

There is some conceptual linkage between vulnerabilities and remediation in the domain model:

- [`Vulnerability.remediation_type`](backend/app/models/vulnerability.py:273)
- [`Vulnerability.remediation_actions`](backend/app/models/vulnerability.py:276)
- [`SecurityService.remediate_vulnerability()`](backend/app/services/security_service.py:201)
- [`SecurityService.verify_remediation()`](backend/app/services/security_service.py:279)

This means the system already tracks **execution of remediation actions** against a vulnerability after a remediation workflow begins.

But the LLM-generated remediation plan is not integrated into that model. Specifically:

- [`Vulnerability`](backend/app/models/vulnerability.py:229) has no `remediation_plan` field
- there is no scan-level or plan-level entity/repository
- there is no linkage like `plan_id`, `scan_id`, `recommended_actions`, or `recommended_priority`
- the generated plan is not used to seed [`remediation_actions`](backend/app/models/vulnerability.py:276)

### Architectural implication

The system has two separate concepts:

1. **detected vulnerability records** persisted in the datastore
2. **generated remediation plan** returned at scan time

These are adjacent, but not integrated.

## Key observation 5: the current plan shape is scan-level, not vulnerability-level

The fallback plan returned by [`_create_remediation_plan()`](backend/app/agents/security_agent.py:1159) has this approximate shape:

- `priority`
- `estimated_time_hours`
- `actions`
- `dependencies`
- `rollback_plan`

This looks like a **single scan-level summary plan** for the whole API, not a per-vulnerability remediation structure.

That design is reasonable if the product goal is:

- “scan an API”
- “produce one prioritized remediation roadmap for that API”

It is less suitable if the product goal is:

- “track remediation guidance for each vulnerability”
- “assign remediation ownership/status/actionability per finding”
- “audit what plan was recommended at the time of detection”

So whether the plan should be stored with vulnerabilities depends on the intended granularity.

## Key observation 6: query/frontend integration is inconsistent and partially broken

In [`QueryService`](backend/app/services/query_service.py:684), security agent insights are attached to query results. The field [`remediation_plan`](backend/app/services/query_service.py:688) is passed through as `agent_result.get("remediation_plan", "")`.

But in the frontend query UI, [`QueryResponse.tsx`](frontend/src/components/query/QueryResponse.tsx:81) treats `remediation_plan` like a string and calls [`substring()`](frontend/src/components/query/QueryResponse.tsx:83) on it.

This is inconsistent with the backend contract, where:

- [`ScanResponse.remediation_plan`](backend/app/api/v1/security.py:40) is a `dict`
- frontend scan type [`ScanResponse.remediation_plan`](frontend/src/types/index.ts:536) is also a structured object

### Consequence

At least one consumer path assumes the remediation plan is plain text while the main API contract exposes it as structured JSON. That mismatch suggests the plan is not well standardized across the product.

This weakens the case for simply “returning all objects” without first defining the canonical shape.

## Key observation 7: MCP documentation appears incomplete for required gateway scoping

The MCP security tool in [`mcp-servers/security_server.py`](mcp-servers/security_server.py:123) calls backend `/security/scan` with only `api_id` in the shown snippet at [`security_server.py`](mcp-servers/security_server.py:171). Meanwhile, the REST endpoint shown in [`backend/app/api/v1/security.py`](backend/app/api/v1/security.py:187) invokes [`scan_api_security()`](backend/app/services/security_service.py:91) with both `gateway_id` and `api_id`.

This may indicate one of the following:

- the MCP layer is targeting a different backend route not shown here
- MCP documentation/tool wiring is stale
- MCP request construction is missing required scoping information

This is adjacent to the remediation-plan discussion, but it reinforces the broader observation that the security scan contract is not fully coherent across surfaces.

## Direct answer: should the remediation plan return all objects?

### Short answer

Not in its current form.

### Why

Because the rest of the system currently models [`remediation_plan`](backend/app/api/v1/security.py:40) as a single object, not a collection. Returning all parsed objects directly would create shape inconsistencies unless the following are updated together:

- [`SecurityAnalysisState`](backend/app/agents/security_agent.py:46)
- [`SecurityAgent._create_remediation_plan()`](backend/app/agents/security_agent.py:1026)
- [`ScanResponse`](backend/app/api/v1/security.py:30)
- frontend [`ScanResponse`](frontend/src/types/index.ts:528)
- any UI and query consumers such as [`QueryResponse.tsx`](frontend/src/components/query/QueryResponse.tsx:54)

### Better options

#### Option A: keep single-plan contract, merge multiple LLM objects into one canonical plan

This is the least disruptive option.

If multiple objects are returned by the LLM, the backend should normalize them into one structure such as:

- overall priority
- consolidated ordered actions
- grouped verification steps
- optional `sources` or `alternatives`

This preserves the single-object contract while avoiding silent data loss.

#### Option B: formally support multiple plans

If the product wants alternatives or segmented plans, then the contract should change deliberately to something like:

- `remediation_plan`: primary normalized plan
- `alternative_plans`: list of additional candidates

or

- `remediation_plans`: array of plans

This requires coordinated backend, API, MCP, and frontend updates.

## Direct answer: should the remediation plan be connected to vulnerabilities and stored?

### Short answer

Yes, but the storage model should match the intended lifecycle.

### Recommended design direction

There are two viable patterns.

#### Pattern 1: store remediation plan at scan level

Best if the plan is meant to describe the whole API scan result.

Suggested model:

- security scan entity/document
- fields: `scan_id`, `gateway_id`, `api_id`, `vulnerabilities`, `remediation_plan`, `analysis_timestamp`, model metadata, prompt/version info

Benefits:

- preserves historical scan outputs
- supports auditability and re-analysis
- avoids duplicating the same plan on every vulnerability document
- matches current scan-level plan shape

This is the cleanest fit for the current implementation.

#### Pattern 2: store remediation guidance on each vulnerability

Best if the product needs remediation tracking per finding.

Suggested additions to [`Vulnerability`](backend/app/models/vulnerability.py:229):

- `recommended_remediation` or `remediation_plan`
- `recommended_priority`
- `verification_steps`
- `plan_generated_at`
- `plan_version` or `scan_id`

Benefits:

- each vulnerability has actionable guidance attached
- easier filtering and workflow orchestration by finding
- aligns better with remediation lifecycle features

Tradeoff:

- if one scan-level plan covers multiple vulnerabilities, storing the whole plan on each vulnerability duplicates data unless normalized carefully

## Recommended architecture

Given the current code, the strongest recommendation is:

1. **Introduce a scan-level persisted entity** for security scan results
2. keep vulnerabilities persisted separately in [`security-findings`](backend/app/db/repositories/vulnerability_repository.py:25)
3. link each vulnerability to `scan_id`
4. persist the normalized remediation plan with the scan record
5. optionally derive per-vulnerability recommended actions from the scan plan later

This approach fits the current implementation best because:

- the plan is currently produced at API-scan scope
- the service already returns a `scan_id` field, though it is placeholder-like in [`security_service.py`](backend/app/services/security_service.py:138)
- vulnerability lifecycle remains independent
- historical plan retention becomes possible

## Specific gaps identified

### 1. Placeholder scan ID
[`SecurityService.scan_api_security()`](backend/app/services/security_service.py:138) returns `str(UUID(int=0))`, which is not a real persisted scan identifier. Without a true scan record, there is no durable parent entity for the remediation plan.

### 2. No remediation-plan repository/entity
There is no repository analogous to [`VulnerabilityRepository`](backend/app/db/repositories/vulnerability_repository.py:19) for scan records or remediation plans.

### 3. No vulnerability-to-scan linkage
[`Vulnerability`](backend/app/models/vulnerability.py:229) has no `scan_id` field, so persisted findings cannot be grouped back to the exact plan that produced them.

### 4. UI contract mismatch
[`QueryResponse.tsx`](frontend/src/components/query/QueryResponse.tsx:83) assumes string behavior for a structured object.

### 5. Silent loss of extra LLM outputs
[`SecurityAgent._create_remediation_plan()`](backend/app/agents/security_agent.py:1147) discards all but one parsed plan.

### 6. Remediation recommendations are not operationalized
The generated plan is not used to initialize [`remediation_actions`](backend/app/models/vulnerability.py:276) or to drive remediation workflows in [`SecurityService.remediate_vulnerability()`](backend/app/services/security_service.py:201).

## Recommended next steps

### Near-term
1. Normalize multiple parsed LLM objects into one canonical plan instead of returning only the first object.
2. Standardize the `remediation_plan` schema and document it explicitly.
3. Fix consumers that treat the plan as a string, especially [`QueryResponse.tsx`](frontend/src/components/query/QueryResponse.tsx:81).

### Medium-term
1. Introduce a persisted security scan record with a real `scan_id`.
2. Store the generated remediation plan in that scan record.
3. Add `scan_id` to [`Vulnerability`](backend/app/models/vulnerability.py:229) so findings can be traced back to the originating plan.

### Longer-term
1. Decide whether remediation should be scan-centric or vulnerability-centric.
2. If vulnerability-centric, derive and persist per-vulnerability recommended actions from the canonical scan plan.
3. Use the stored plan to bootstrap remediation workflows and audit trails.

## Final assessment

The current implementation is halfway between two designs:

- a **single scan-level remediation roadmap**
- a **finding-oriented remediation workflow**

Because of that, the system currently generates useful remediation content but does not treat it as first-class persisted domain data.

The strongest overall observation is:

- returning only the first parsed plan is lossy
- returning all plans immediately would break current contracts
- the remediation plan should be persisted
- the best current fit is to persist it at **security scan level**, then link vulnerabilities to that scan
- per-vulnerability integration can be added on top once the domain contract is clarified