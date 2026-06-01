# WORKING-AGREEMENT.md — How AI works in this project

## Core rule: spec before code

Before touching a single line of code, the AI always:

1. **Analyzes** — reads the relevant context (`CONTEXT.md`, affected module, contracts, current code)
2. **Summarizes** — explains to the human what it understood about the current state and the request
3. **Proposes** — describes the change it's going to make: affected files, decisions taken, identified risks, alternatives discarded
4. **Waits for approval** — explicit, from the human, before modifying any file
5. **Documents** — updates the spec for the module / feature BEFORE writing code
6. **Implements** — only then writes code following the approved spec

## Why

- **Without prior spec:** AI improvises, mixes decisions, leaves invisible debt
- **With prior spec:** human validates intent before burning tokens, leaves a record for future sessions, other agents can pick up the work

This rule applies to EVERY change: bootstrap, new feature, bug fix, refactor, even things that look trivial. Always a spec first.

## Exceptions

Only two:
- Questions that DO NOT modify code (answer, explain, summarize)
- Cosmetic changes done in batch (rename variable, format) — agent groups them and explains before pushing

## How it looks in practice

**Bad (no agreement):**
> User: "add Google sign-in"
> AI: *creates files, writes code, commits*

**Good (with agreement):**
> User: "add Google sign-in"
> AI: *reads `CONTEXT.md`, contracts of the `auth/` module*
> AI: "I see the project uses Firebase for auth. I propose:
> - Add `signInWithGoogle()` in `auth/firebase.ts`
> - Button in `LoginModal.svelte` above email/password
> - Spec at `modules/auth/specs/google-signin.md`
> Risk: popup is blocked in VS Code webview (known issue).
> Should I proceed like this or do you prefer a different flow?"
> User: "yes, go ahead"
> AI: *writes spec, waits for ok, writes code, commits*

---

## Why this matters in this blueprint

This blueprint is DDD lite, SDD and modular architecture put into practice. The AI generates the methodology (specs, contracts, architecture) from your idea instead of you writing it by hand.

But that only works if the AI **never skips the spec step**. Without this rule, the blueprint becomes another vibe-coding tool with extra ceremony. With it, every change is grounded in a spec, every spec lives in the repo, and the project stays coherent across sessions and across agents.
