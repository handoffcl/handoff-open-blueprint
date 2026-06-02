---
name: code-quality
description: Run a code quality review — checks consistency, dead code, test coverage gaps, type safety, error handling, and readability. Adapts to the project's actual stack and quality rules defined in CLAUDE.md.
---

# Code Quality Review

> **Working agreement** — Before doing anything, read `WORKING-AGREEMENT.md` at the repo root. The rule applies here too: analyze → summarize → propose → wait for OK → write the spec → only then act. If `WORKING-AGREEMENT.md` doesn't exist yet, create it from the blueprint's template.

You are reviewing this project for code quality. Read `CLAUDE.md` first — it defines the project's own quality rules. Your job is to check whether the project follows its own standards, then flag anything beyond that.

---

## Step 1 — Read the project's own rules

Read `CLAUDE.md`. Note:
- Linting tools and how to run them
- Type checking requirements
- Test commands
- Naming conventions
- What the project explicitly says NOT to do

Then run the quality gate:
```bash
# If defined in Makefile:
make quality

# Otherwise run what CLAUDE.md specifies
```

Report the output verbatim if there are errors.

---

## Step 2 — Code consistency

Check across the codebase for:
- [ ] Inconsistent naming conventions (camelCase vs snake_case mixed, etc.)
- [ ] Functions doing too many things (hard to name precisely = doing too much)
- [ ] Copy-pasted logic that should be a shared function
- [ ] Inconsistent error handling (some routes return 400, others raise exceptions for the same case)
- [ ] Magic numbers or strings without constants
- [ ] Different patterns for the same operation in different files

---

## Step 3 — Dead code & bloat

- [ ] Unused imports
- [ ] Functions defined but never called
- [ ] Commented-out code blocks
- [ ] `TODO` / `FIXME` comments older than the last 5 commits
- [ ] Config options that are never read
- [ ] Feature flags that are always on or always off

---

## Step 4 — Type safety

For typed languages (Python with mypy, TypeScript):
- [ ] Are there `Any` types that could be narrowed?
- [ ] Are there unchecked casts or forced type assertions (`as Type`)?
- [ ] Are external data sources (API responses, DB rows) typed at the boundary?
- [ ] Are optional values (`None` / `undefined`) handled explicitly?

---

## Step 5 — Error handling

- [ ] Are errors propagated or silently swallowed?
- [ ] Do error responses include enough context for debugging without leaking internals?
- [ ] Are external calls (APIs, DB) wrapped with appropriate error handling?
- [ ] Are there bare `except:` or `catch (e: any)` catching everything?
- [ ] Are user-facing errors in the user's language and actionable?

---

## Step 6 — Test coverage gaps

Don't just measure coverage percentage. Find the gaps that matter:
- [ ] Are happy paths tested?
- [ ] Are edge cases tested (empty input, max values, invalid types)?
- [ ] Are error paths tested (what happens when external service fails)?
- [ ] Are business rules tested directly, not just through API endpoints?
- [ ] Are tests independent (no shared mutable state between tests)?

---

## Step 7 — Readability

- [ ] Can you understand what a function does without reading its body? (name + signature)
- [ ] Are complex conditions extracted into named variables?
- [ ] Are comments explaining *why*, not *what*?
- [ ] Are there comments that are now wrong (code changed, comment didn't)?

---

## Step 8 — Report

Group findings by file. For each issue:

```
File: path/to/file.py:line_number
Issue: What's wrong
Fix: Specific change (include code snippet if helpful)
```

Categories: `consistency` / `dead-code` / `types` / `error-handling` / `tests` / `readability`

---

## Step 9 — Summary

1. Did `make quality` pass? If not, list the errors.
2. Total issues by category
3. Top 3 to fix first
4. One line on the overall code quality health
