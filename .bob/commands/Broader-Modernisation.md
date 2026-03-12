# Modernization Verification Prompt (Whole Application)

Scan the current workspace and determine whether a **modernization/migration** has occurred (e.g., Java → Node/TypeScript, monolith → services, framework upgrades, infra/containerization changes).

Your goal is to produce a concise **Modernization Evidence Extract** that reviewers can use to verify “before vs after” from the repo.

## What to check
1. **Tech Stack Identification (Current State)**
   - Primary languages/frameworks (backend + frontend)
   - Build tools (e.g., Maven/Gradle → npm/pnpm, etc.)
   - Runtime/containerization (Docker/K8s/serverless)
   - Key entrypoints (main server/app start files)

2. **Modernization Signals**
   Detect and summarize evidence such as:
   - Language/runtime migration (e.g., `.java`/`pom.xml` reduced, Node/TS files added)
   - Build/dependency changes (Maven/Gradle → npm; dependency lockfiles)
   - Framework changes (Spring → Express/Nest; JSP → React; etc.)
   - Architecture shifts (monolith → modular/services; new gateways; new workers)
   - CI/CD + IaC changes (new pipelines, Dockerfiles, Terraform, Helm, etc.)
   - API contract changes (routes moved/rewritten, schema changes)

3. **Before vs After (Repo Evidence)**
   - List “Before” indicators (legacy folders/files/configs still present)
   - List “After” indicators (new platform folders/files/configs)
   - If the repo contains both, explain coexistence (strangler pattern, staged migration)

4. **Impact Summary (High-level)**
   - What improved (maintainability, deployability, performance, security posture)
   - What might be incomplete / risky (gaps, parity concerns)

## Required output format (Markdown)
Write a Markdown report suitable for `docs/Modernisation.md` containing:

- **Modernization Summary (1 paragraph)**
- **Detected Stack (Current)**
- **Migration Detected?** (Yes/No/Partial + confidence)
- **Evidence Table**
  | Claim | Evidence (file paths) | Notes |
- **Key Diffs**
  - Build & tooling changes
  - Runtime/framework changes
  - Architecture changes
- **What to Review Next** (short checklist)

## Rules
- Use only what can be supported by the workspace contents.
- Reference concrete file paths (e.g., `backend/package.json`, `pom.xml`, `src/main/java/...`, `services/api/...`).
- Ignore test/vendor/generated directories (`tests/`, `vendor/`, `dist/`, `build/`, `node_modules/`, `.venv/`).
- If you cannot find proof for a claim, label it **Assumption**.

Save the final output as: `docs/Modernisation.md`.
