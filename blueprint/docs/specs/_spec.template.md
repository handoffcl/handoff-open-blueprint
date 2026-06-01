# Spec: {{FEATURE_NAME}}
<!-- status: pending | {{DATE}} -->

> Write this spec **before** writing code.
> The spec is the contract — the code implements it, not the other way around.
> When spec and code diverge, the spec wins (update one or the other intentionally).

---

## Context

_Why does this feature exist? What problem does it solve? Who asked for it?_

---

## Input

| Field | Type | Required | Notes |
|---|---|---|---|
| `{{field}}` | `{{type}}` | Yes/No | {{notes}} |

---

## Output

```json
{
  "{{field}}": "{{type}}",
  "{{field}}": "{{type}}"
}
```

---

## Behavior

_Step-by-step description of what the feature does:_

1. {{STEP_1}}
2. {{STEP_2}}
3. {{STEP_3}}

---

## Edge cases

| Case | Expected behavior |
|---|---|
| {{EDGE_CASE_1}} | {{EXPECTED_1}} |
| {{EDGE_CASE_2}} | {{EXPECTED_2}} |
| Empty input | Return 400 with structured error |
| Input exceeds limits | Reject early, before any expensive processing |

---

## Cost / performance constraints

_If this feature calls external APIs or has performance requirements:_

- Max latency: {{MAX_LATENCY}}
- Cost per call: ~{{COST}}
- Rate limit: {{RATE_LIMIT}}

---

## What this spec does NOT cover

- {{OUT_OF_SCOPE_1}}
- {{OUT_OF_SCOPE_2}}

---

## Implementation notes

_Optional: hints for the implementer (not requirements — the spec above is the requirement)._

---

## Test scenarios

- [ ] Happy path: {{HAPPY_PATH}}
- [ ] Edge case: {{EDGE_CASE}}
- [ ] Error case: {{ERROR_CASE}}
