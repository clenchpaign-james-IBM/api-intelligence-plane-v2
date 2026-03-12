# Business Context Prompt (Epics + User Stories)

Scan the current workspace. Analyze the source code and configuration to automatically identify **implemented product capabilities**. Infer features from routes/endpoints, services, UI components, workflows, jobs, and configs.

Organize the results into **Agile Epics** (business-level outcomes) with nested **User Stories** (what users can do). Use sensible defaults if roles or details aren’t explicit.

## Output requirements
1. **Product Summary**
   - What the product does (1–2 paragraphs)
   - Who uses it (primary roles/personas)

2. **Epics and User Stories**
   - Group by **Epic** (high-level business functionality)
   - Under each Epic, list **User Stories** in standard format:
     - “As a [role], I want [capability], so that [benefit].”
   - For each story, include **Acceptance Criteria** (2–5 bullets) that are testable and specific.

3. **Cross-cutting / Technical Epics**
   Capture cross-cutting concerns as technical stories (e.g., authentication/authorization, security controls, audit logging, performance, observability, reliability, data retention).

4. **Traceability**
   - Where possible, reference relevant **file paths/modules** that indicate the feature (e.g., routes, controllers, services, UI pages).
   - If a capability is inferred but not explicit, label it as **Assumption**.

## Exclusions
- Ignore test directories, vendor directories, build outputs, and generated code (e.g., `test/`, `tests/`, `vendor/`, `dist/`, `build/`, `node_modules/`, `.venv/`, `__pycache__/`).

## Format
- Output in **Markdown** with:
  - Epic headings
  - Nested bullet points for stories
  - Acceptance criteria under each story
- Save as: `docs/business-context.md`.
