# Philosophy — Why this blueprint exists

## The problem with vibecoding

Vibecoding — building apps by talking to an AI — is real and it works. But it has a critical flaw:

**Every session starts from zero.**

You open your AI agent, start a new conversation, and the first thing you do is spend 10-15 minutes explaining:
- What the project does
- What decisions were made and why
- What was built last session
- What NOT to touch
- What's next

That's not building. That's paying to re-explain your own project to your own tool.
At $3-15 per million tokens, that's expensive. At 30-60 minutes per week, that's a lot of time.

---

## How the AI works in this blueprint

Spec before code. Always. No exceptions.

Before any change, the AI:
1. Reads the project context and the affected module
2. Proposes what it will do (with risks and alternatives)
3. Waits for human approval
4. Documents the decision in the corresponding spec
5. Only then writes code

See `WORKING-AGREEMENT.md` for the full flow and the few cases where something different applies.

Why this rule? Because without it the AI improvises, mixes decisions, and leaves debt that only shows up later. With it, the human validates intent before burning tokens, and the resulting spec serves future sessions and other agents.

---

## The insight

The best developers don't carry everything in their heads. They write things down — architecture docs, ADRs, specs — so that anyone (including their future self) can understand the system without asking.

**The same principle applies to AI-assisted development, but more strictly.**

An AI doesn't have memory that persists between sessions. It needs to reconstruct context from what it can read. If your repo is well-documented, the AI is productive immediately. If it's not, you pay the context tax every single session.

---

## What this blueprint does

It makes your repo **self-documenting for AI**. Not just for humans — for AI.

The difference:
- Human docs explain *what* the system does
- AI-optimized docs also explain *what decisions were made*, *why*, and *what not to do*

That last part is crucial. An AI that doesn't know what decisions were already made will re-open them. An AI that doesn't know what not to touch will touch it. An AI that doesn't know *why* something was built a certain way will refactor it into something worse.

---

## The CONTEXT.md idea

Every project has a `CONTEXT.md` — a living document that captures:
- Current state of the project
- Key decisions and why they were made
- What's done, what's in progress, what's next
- What NOT to do (and why)
- Where to find things

This file is auto-updated after every commit (git post-commit hook) and optionally after every session (if your AI agent supports session-end hooks). It's never stale because it updates itself.

**Result:** the AI reads the file and starts working immediately — no re-explaining, no wrong assumptions, no re-opening closed decisions.

---

## All docs are living docs

In v2, the auto-update system extends beyond CONTEXT.md. Every structural doc updates itself:

| Doc | Auto-updated section | What it captures |
|---|---|---|
| `CONTEXT.md` | `## Recent Changes` | Last commits classified by type |
| `constitution.md` | `## Project Status` | Phase, feature count, last decision |
| `assumptions.md` | `## Last Review` | Staleness warning, open question count |
| `plan/v1-mvp.md` | `## Build Progress` | Total commits, features shipped, last feature |
| `specs/*.md` | `<!-- status -->` marker | Whether spec is being actively developed |

The rest of each doc (principles, decisions, open questions) remains manual — those require human judgment. Only the measurable status sections update automatically.

---

## The greenfield problem

SpecKit and SDD are powerful — but they assume you arrive with a clear vision.

**For a product built from zero, reality is different:**
- The idea mutates as you build
- What you thought was an immutable principle on day 1 gets revised by week 3
- The specs you wrote in week 1 are obsolete by week 2
- The architecture you planned doesn't match what the product became

Traditional blueprints treat docs as *input* documents — written before the project starts, frozen after.
This blueprint treats all docs as *living* documents — they start minimal and evolve with the project.

**Two phases, same docs:**

| Phase | Characteristics | What changes |
|---|---|---|
| Exploratory | <20 commits, idea still mutating | Everything — even the constitution |
| Stable | ≥20 commits, core design settled | Specs and ADRs, not principles |

The `update_docs.py` script detects phase from commit count and updates the Project Status section accordingly. It also warns when structural docs haven't been manually updated in a long time — a signal that reality may have outrun the documentation.

---

## Spec-driven development (SpecKit)

**Write the spec before you write the code.**

Not because it's "proper software engineering" — because it makes the AI write better code.

When the AI has a spec that says:
> "The validation pipeline has 4 layers. Layer 1 is format/size (no cost). Layer 2 is local pixel analysis (no cost). Layer 3 is a cheap AI precheck (~$0.001). Layer 4 is full AI analysis (~$0.025). Each layer only runs if the previous one passed."

...it writes code that implements exactly that. Without the spec, it writes whatever seems reasonable, which may or may not match what you had in mind.

Specs are cheap to write (10-20 minutes). Fixing code that doesn't match what you meant is expensive.

The spec lives in `docs/specs/<feature>.md`. The `<!-- status -->` marker in the header auto-updates to reflect whether the spec is being actively developed (`in-progress`) or not yet started (`pending`).

---

## Modular architecture

Modules with clear contracts mean the AI knows exactly what it can and can't change.

When a module has a defined interface:
```
evaluator.py → returns AdjustedData
policy.evaluate(data, adjusted) → returns PolicyResult
```

The AI can change the internals of any module without breaking others. Without clear contracts, every change is a potential cascade.

---

## The quality gate

`make quality` runs linters + type checker + tests before every commit. This isn't optional.

The reason: AI agents write code fast — sometimes too fast. The quality gate catches:
- Type errors that would surface in production
- Style inconsistencies that accumulate into unreadable code
- Regressions in existing functionality

With CI running the same checks on GitHub, nothing broken ever reaches main.

---

## Structured Vibe Coding

This is the name for what this blueprint enables.

Traditional vibecoding: fast but chaotic. The AI builds without memory of why it built what it built. Decisions get re-opened. Work gets duplicated. Context evaporates between sessions.

Structured Vibe Coding keeps the speed and freedom of vibecoding, but adds:

| What | How |
|---|---|
| **Structure that builds itself** | Docs auto-update after every commit |
| **Guidance that evolves** | Specs, constitution, and ADRs grow with the product |
| **Context that never expires** | CONTEXT.md always reflects the current state |
| **Decisions that don't repeat** | ADRs document why — the AI won't re-suggest what was already decided |

The best development workflow right now:

1. Human arrives with an idea
2. Blueprint structures everything from scratch (via `/bootstrap-app`)
3. Human and AI design together (constitution, specs, ADRs)
4. AI implements — guided by specs
5. AI verifies — quality gate passes
6. Everything documents itself — hooks run, docs update
7. Next session: the AI reads the docs, starts working in 30 seconds

**This is not replacing developers.** It removes the parts that slow developers down —
boilerplate, repetitive implementation, context-switching overhead —
while keeping the parts that require human judgment: defining problems, setting constraints, making architectural decisions.

The developer who masters this workflow builds faster without sacrificing quality or stability.
And unlike traditional vibecoding, the project stays coherent as it grows — because the documentation grows with it.
