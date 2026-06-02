---
name: security-review
description: Run a security review on the current project — checks for OWASP Top 10, auth issues, secrets exposure, injection vulnerabilities, and domain-specific risks based on what the project does.
---

# Security Review

> **Working agreement** — Before doing anything, read `WORKING-AGREEMENT.md` at the repo root. The rule applies here too: analyze → summarize → propose → wait for OK → write the spec → only then act. If `WORKING-AGREEMENT.md` doesn't exist yet, create it from the blueprint's template.

You are a security auditor reviewing this project. Be specific — no generic checklists. Every finding must reference the actual file and line where the issue exists.

---

## Step 1 — Understand the project

Read `CONTEXT.md` first. Identify:
- What the project does and who uses it
- What data it handles (PII, financial, health, credentials)
- What external systems it integrates with (auth, payments, AI APIs, storage)
- What the attack surface is (public API, admin panel, file upload, webhooks, etc.)

---

## Step 2 — Run the review

Check each category below. Skip categories that don't apply to this project.

### Authentication & Authorization
- [ ] Are all routes protected that should be?
- [ ] Is session management correct (cookie flags: HttpOnly, Secure, SameSite)?
- [ ] Are admin endpoints behind a separate auth check?
- [ ] Are API keys validated server-side, not just client-side?
- [ ] Is there protection against brute force / rate limiting on login?

### Injection
- [ ] Are all database queries parameterized? (No string concatenation in SQL)
- [ ] Is user input sanitized before use in shell commands?
- [ ] Is there XSS protection on any HTML rendering of user content?
- [ ] Are file paths from user input validated to prevent path traversal?

### Secrets & Configuration
- [ ] Are there any hardcoded secrets, API keys, or passwords in the code?
- [ ] Is `.env` gitignored? Is `.env.example` the only committed variant?
- [ ] Are secrets loaded from environment variables, not config files?
- [ ] Are error messages sanitized — no stack traces or internal paths exposed to users?

### Data Protection
- [ ] Is sensitive data (PII, documents, credentials) stored minimally and necessary?
- [ ] Is data encrypted at rest if the domain requires it?
- [ ] Are logs free of sensitive data (RUT, names, tokens, keys)?
- [ ] Are file uploads validated for type, size, and content?

### External Integrations
- [ ] Are webhooks validated with signatures before processing?
- [ ] Are third-party API responses validated before use?
- [ ] Are redirect URLs validated to prevent open redirect attacks?
- [ ] Is SSRF possible via any user-controlled URL inputs?

### AI-specific (if the project uses LLMs)
- [ ] Is user input sanitized before being included in prompts?
- [ ] Are prompt injection attacks considered for user-facing AI features?
- [ ] Is the AI output validated before acting on it (especially for agentic flows)?
- [ ] Are costs capped per user/request to prevent abuse?

### Dependencies
- [ ] Are there known vulnerable packages? (Run `pip audit` or `npm audit`)
- [ ] Are dependency versions pinned?

---

## Step 3 — Report findings

For each issue found:

```
[SEVERITY] Category — Short description
File: path/to/file.py:line_number
Issue: What's wrong and why it's a risk
Fix: Specific change needed
```

Severity levels:
- **CRITICAL** — exploitable now, no authentication needed, data breach risk
- **HIGH** — exploitable with some effort, significant impact
- **MEDIUM** — limited impact or requires specific conditions
- **LOW** — defense-in-depth, hardening, good practice

---

## Step 4 — Summary

End with:
1. Total findings by severity
2. Top 3 to fix first (highest impact/effort ratio)
3. One sentence on the overall security posture of the project
