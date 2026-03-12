# Simple FedRAMP Evidence Report Prompt

Scan the current workspace. Analyze source code, configs, deployment files (Docker/K8s/Terraform/etc.), and CI/CD to create a **simple FedRAMP readiness evidence report** (Hackathon-level, not official certification).

## Include (keep short)
1. **What the system is**
   - 3–6 bullets: main parts (UI, API, DB, workers, integrations)
   - Where it runs (local/cloud/container/serverless)

2. **Security checklist (with evidence)**
   For each item below, answer:
   - Status: **Implemented / Partial / Missing**
   - Evidence: file paths (or **Assumption** if not found)

   Checklist:
   - Login / identity (AuthN)
   - Permissions / roles (AuthZ)
   - Secrets handling (no hardcoded secrets, secret manager or env vars)
   - Encryption in transit (TLS) and at rest (DB/storage if configured)
   - Audit logging (who did what, when) + correlation/request IDs if available
   - Monitoring/alerting hooks (logs/metrics/traces or integrations)
   - Secure config defaults (CORS, headers, input validation, rate limits)
   - Dependency/security checks in CI (SCA/SAST/tests) if present
   - Backup/recovery or basic reliability (if present)

3. **Top risks & next steps**
   - 5 bullets max: biggest gaps + what to do next (POA&M-style)

## Rules
- Only claim what you can prove from the repo.
- Reference concrete file paths (e.g., `auth/middleware.ts`, `infra/`, `.github/workflows/`, `Dockerfile`, `k8s/`).
- Ignore `tests/`, `vendor/`, `dist/`, `build/`, `node_modules/`, `.venv/`.

## Output
Write a single Markdown file: `docs/FEDRAMP-Report.md`.
