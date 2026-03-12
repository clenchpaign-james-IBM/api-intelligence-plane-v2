# Whole-Product Engineering Prompt

Scan the current workspace. Analyze all source code and configs to understand the **overall product architecture** and **major features** (not a component-by-component spec).

Generate a clear, high-level **architecture + features** document in Markdown.

## Include
1. **Product Overview**
   - What the product is and who it’s for
   - Top 5–10 capabilities/features (broad level)

2. **Architecture at a Glance**
   - Main parts (UI, API/services, data stores, background jobs, integrations)
   - How they connect (1–2 paragraphs)

3. **Key Flows**
   - 3–6 important user/system flows (e.g, “User signs in”, “Core workflow”, “Admin action”, “Background processing”)
   - For each flow: short step list + which components participate

4. **Data & Integrations**
   - What data is stored where (just the big pieces)
   - External systems/APIs and what they’re used for

5. **Deployment & Environments (brief)**
   - Where it runs, key services
   - How it’s built/deployed (CI/CD at a glance)

6. **Operational Notes (brief)**
   - Logging/monitoring basics
   - Common failure points / risks (short list)

## Output rules
- Keep it simple and skimmable (headings + bullets).
- Prefer what can be proven from the workspace; mark unknowns as **Assumption**.
- Add a short **“Source Pointers”** section linking major features/components to key folders/files.

Write the final output as a single Markdown file: `docs/engineering.md'
