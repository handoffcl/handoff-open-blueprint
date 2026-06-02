---
name: architecture-review
description: Review the project's architecture and development patterns — evaluates module boundaries, data flow, coupling, scalability constraints, and recommends patterns that fit this specific project's domain and stage.
---

# Architecture & Patterns Review

> **Working agreement** — Before doing anything, read `WORKING-AGREEMENT.md` at the repo root. The rule applies here too: analyze → summarize → propose → wait for OK → write the spec → only then act. If `WORKING-AGREEMENT.md` doesn't exist yet, create it from the blueprint's template.

You are a senior architect reviewing this project. Read the actual code, not just the docs. Every recommendation must be grounded in what exists — no hypothetical refactors for problems the project doesn't have.

---

## Step 1 — Understand context

Read in this order:
1. `CONTEXT.md` — current state, modules, key decisions
2. `docs/constitution/constitution.md` — immutable principles
3. `docs/plan/v1-mvp.md` — ADRs already made
4. Project structure (list top-level dirs and key files)

Identify:
- Project stage (exploratory / growing / stable)
- Team size implied by the codebase
- Domain complexity (simple CRUD vs complex rules vs AI pipelines)

---

## Step 2 — Evaluate architecture

### Module boundaries
- Are modules clearly separated with defined inputs/outputs?
- Is there circular dependency between modules?
- Does `api/` contain business logic it shouldn't?
- Are there god objects or god modules that know too much?

### Data flow
- Is the data flow from input to output traceable?
- Are there multiple sources of truth for the same data?
- Is state managed consistently (server-side vs client-side)?

### Coupling & cohesion
- Are changes to one module likely to break another?
- Are modules too small (over-fragmented) or too large (under-split)?
- Is there shared mutable state across modules?

### Scalability constraints
- What breaks first under load? (identify the bottleneck)
- Are there N+1 query patterns?
- Are expensive operations (AI calls, PDF generation, external APIs) async?
- Is there caching where it matters?

### AI pipeline (if applicable)
- Is there a cost gate before expensive model calls?
- Are prompts versioned or hardcoded strings?
- Is there retry logic with backoff for flaky API calls?
- Are responses validated before being acted upon?

---

## Step 3 — Evaluate patterns in use

For each pattern found, assess: **Is this the right pattern for this project at this stage?**

Common patterns to check:
- **Policy pattern** — good for variant business rules (e.g. per-bank policies)
- **Repository pattern** — good when storage might change; overkill for simple CRUD
- **Event-driven** — good for decoupling; overhead for simple flows
- **Layered architecture** — appropriate separation? or artificial?
- **Feature flags** — needed? or premature complexity?

---

## Step 4 — Recommend

For each recommendation:

```
[PRIORITY] Pattern/Change — Short description
Current: what exists now
Problem: what this causes (concrete, not hypothetical)
Recommendation: specific change with example
Effort: low / medium / high
```

Priority levels:
- **NOW** — causing bugs or blocking growth today
- **SOON** — will become a problem within the next 10 features
- **LATER** — good practice, low urgency, address when passing through

---

## Step 5 — Summary

End with:
1. Architecture score (1–5) with one sentence justification
2. The single most important structural change to make next
3. What the project is doing well architecturally — don't only find problems
