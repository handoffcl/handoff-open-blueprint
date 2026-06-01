#!/usr/bin/env python3
"""
update_docs.py v2 — Keeps all living docs in sync after every commit.

Triggered by:
  - git post-commit hook
  - AI agent session-end hook (onSessionEnd in .handoff/settings.json)

Surgically updates (never overwrites full files):
  - CONTEXT.md                    → ## Recent Changes
  - docs/constitution/*.md        → ## Project Status
  - docs/clarify/assumptions.md   → ## Last Review
  - docs/plan/v1-mvp.md           → ## Build Progress
  - docs/specs/*.md               → <!-- status: ... --> marker in header

Creates stub docs for any that don't exist yet (greenfield support).

Language: set BLUEPRINT_LANG=es in .blueprint file or environment var (default: en)
"""

from __future__ import annotations

import os
import re
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
MAX_COMMITS = 8


# ── Language ──────────────────────────────────────────────────────────────────


def _load_lang() -> str:
    """Read BLUEPRINT_LANG from .blueprint config file, then env, default 'en'."""
    config = ROOT / ".blueprint"
    if config.exists():
        for line in config.read_text(encoding="utf-8").splitlines():
            if line.startswith("BLUEPRINT_LANG="):
                return line.split("=", 1)[1].strip().lower()
    return os.environ.get("BLUEPRINT_LANG", "en").lower()


LABELS: dict[str, dict[str, str]] = {
    "en": {
        "recent_changes": "Recent Changes",
        "project_status": "Project Status",
        "last_review": "Last Review",
        "build_progress": "Build Progress",
        "pending_specs": "Specs Needed",
        "working_agreement": "Working Agreement (active)",
        "auto_updated": "Auto-updated",
        "features": "Features",
        "fixes": "Fixes",
        "infra_docs": "Infra / Docs",
        "other": "Other",
        "most_modified": "Most Modified Files",
        "phase": "Phase",
        "phase_exploratory": "Exploratory",
        "phase_stable": "Stable",
        "features_shipped": "Features shipped",
        "fixes_applied": "Fixes applied",
        "last_feature": "Last feature",
        "open_questions": "Open questions detected",
        "stale_warning": "⚠️ Not manually updated in",
        "stale_unit": "commits — consider reviewing this doc",
        "pending_specs_none": "All recent src/ changes have a corresponding spec. ✓",
        "pending_specs_intro": "Recent src/ changes with no matching spec — write the spec before the next commit:",
        "wa_rule": "**Rule: analyze → propose → wait for OK → write spec → only then code.**",
        "wa_reminder": "Do NOT write code before a spec exists in `docs/specs/`. This rule applies even in long sessions.",
    },
    "es": {
        "recent_changes": "Últimos cambios",
        "project_status": "Estado del proyecto",
        "last_review": "Última revisión",
        "build_progress": "Progreso de construcción",
        "pending_specs": "Specs pendientes",
        "working_agreement": "Working Agreement (activo)",
        "auto_updated": "Actualizado automáticamente",
        "features": "Features",
        "fixes": "Fixes",
        "infra_docs": "Infra / Docs",
        "other": "Otros",
        "most_modified": "Archivos más modificados",
        "phase": "Fase",
        "phase_exploratory": "Exploratoria",
        "phase_stable": "Estable",
        "features_shipped": "Features completadas",
        "fixes_applied": "Fixes aplicados",
        "last_feature": "Última feature",
        "open_questions": "Preguntas abiertas detectadas",
        "stale_warning": "⚠️ Sin actualización manual en",
        "stale_unit": "commits — considera revisar este documento",
        "pending_specs_none": "Todos los cambios recientes en src/ tienen spec correspondiente. ✓",
        "pending_specs_intro": "Cambios recientes en src/ sin spec — escribe la spec antes del próximo commit:",
        "wa_rule": "**Regla: analiza → propone → espera OK → escribe spec → solo entonces codea.**",
        "wa_reminder": "NO escribas código sin que exista una spec en `docs/specs/`. Esta regla aplica incluso en sesiones largas.",
    },
}

# Section headers the script recognizes in either language.
# Allows switching LANG without breaking existing docs.
_KNOWN_HEADERS: dict[str, list[str]] = {
    "recent_changes": ["Recent Changes", "Últimos cambios", "Latest changes"],
    "project_status": ["Project Status", "Estado del proyecto"],
    "last_review": ["Last Review", "Última revisión"],
    "build_progress": ["Build Progress", "Progreso de construcción"],
    "pending_specs": ["Specs Needed", "Specs pendientes"],
    "working_agreement": ["Working Agreement (active)", "Working Agreement (activo)"],
}


# ── Git helpers ───────────────────────────────────────────────────────────────


def _git(cmd: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT)] + cmd, capture_output=True, text=True
    )
    return result.stdout.strip()


def _recent_commits(n: int = MAX_COMMITS) -> list[dict[str, str]]:
    """Last N commits with hash, message, date, and changed files."""
    log = _git(["log", f"-{n}", "--format=%H|%s|%ad", "--date=short"])
    commits: list[dict[str, str]] = []
    for line in log.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            hash_, msg, date = parts
            files = _git(["diff-tree", "--no-commit-id", "-r", "--name-only", hash_])
            commits.append({"hash": hash_[:7], "msg": msg, "date": date, "files": files})
    return commits


def _commit_count() -> int:
    """Total commits in this repo."""
    try:
        return int(_git(["rev-list", "--count", "HEAD"]))
    except ValueError:
        return 0


def _commits_since_file_changed(file_path: Path) -> int:
    """Commits since file was last git-modified. 0 if untracked."""
    rel = str(file_path.relative_to(ROOT))
    log = _git(["log", "--oneline", "--", rel])
    if not log:
        return 0
    last_hash = log.splitlines()[0].split()[0]
    try:
        return int(_git(["rev-list", "--count", f"{last_hash}..HEAD"]))
    except ValueError:
        return 0


# ── Section surgery ───────────────────────────────────────────────────────────


def _replace_section(
    content: str, section_key: str, new_content: str, L: dict[str, str]
) -> str:
    """
    Find and surgically replace a section in a markdown file.
    Tries the current-language header first, then all known alternatives.
    If no match is found, appends the section at the end.
    """
    candidates = [f"## {L[section_key]}"] + [
        f"## {h}" for h in _KNOWN_HEADERS.get(section_key, [])
    ]
    for header in candidates:
        escaped = re.escape(header.lstrip("# ").strip())
        pattern = rf"(#{{1,3}} {escaped}.*?)(?=\n#{{1,2}} |\Z)"
        m = re.search(pattern, content, re.DOTALL)
        if m:
            return content[: m.start()] + new_content + content[m.end() :]
    return content.rstrip() + "\n\n---\n\n" + new_content


# ── CONTEXT.md ────────────────────────────────────────────────────────────────


def _classify_commits(commits: list[dict[str, str]]) -> dict[str, list[str]]:
    """Classify commits by conventional commit prefix."""
    classified: dict[str, list[str]] = {
        "features": [],
        "fixes": [],
        "docs": [],
        "infra": [],
        "other": [],
    }
    for c in commits:
        msg = c["msg"].lower()
        entry = f"`{c['hash']}` {c['msg']} ({c['date']})"
        if msg.startswith("feat"):
            classified["features"].append(entry)
        elif msg.startswith("fix"):
            classified["fixes"].append(entry)
        elif msg.startswith("docs") or msg.startswith("blueprint"):
            classified["docs"].append(entry)
        elif any(k in msg for k in ("ci", "deploy", "infra", "make", "chore")):
            classified["infra"].append(entry)
        else:
            classified["other"].append(entry)
    return classified


def _build_recent_changes(commits: list[dict[str, str]], L: dict[str, str]) -> str:
    """Build the Recent Changes section for CONTEXT.md."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    classified = _classify_commits(commits)

    lines = [f"## {L['recent_changes']}\n", f"_{L['auto_updated']}: {now}_\n"]

    if classified["features"]:
        lines += [f"\n### {L['features']}"] + [f"- {e}" for e in classified["features"]]
    if classified["fixes"]:
        lines += [f"\n### {L['fixes']}"] + [f"- {e}" for e in classified["fixes"]]
    if classified["infra"] or classified["docs"]:
        lines += [f"\n### {L['infra_docs']}"] + [
            f"- {e}" for e in classified["infra"] + classified["docs"]
        ]
    if classified["other"]:
        lines += [f"\n### {L['other']}"] + [f"- {e}" for e in classified["other"]]

    all_files: list[str] = [f for c in commits for f in c["files"].splitlines()]
    if all_files:
        top = Counter(all_files).most_common(5)
        lines += [f"\n### {L['most_modified']}"] + [f"- `{f}` ({n}x)" for f, n in top]

    return "\n".join(lines) + "\n"


def _src_files_without_spec(commits: list[dict[str, str]]) -> list[str]:
    """Return src/ files changed recently that have no matching spec."""
    specs_dir = ROOT / "docs" / "specs"
    spec_words: set[str] = set()
    if specs_dir.exists():
        for spec in specs_dir.glob("*.md"):
            if not spec.name.startswith("_"):
                for w in re.split(r"[-_]", spec.stem.lower()):
                    if len(w) > 3:
                        spec_words.add(w)

    changed_src = sorted({
        f for c in commits for f in c["files"].splitlines()
        if f.startswith("src/") and not f.endswith((".pyc", ".map"))
    })

    unmatched = [
        f for f in changed_src
        if not any(w in f.lower() for w in spec_words)
    ]
    return unmatched


def _build_pending_specs(commits: list[dict[str, str]], L: dict[str, str]) -> str:
    """Build the Specs Needed section for CONTEXT.md."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    unmatched = _src_files_without_spec(commits)
    lines = [f"## {L['pending_specs']}\n", f"_{L['auto_updated']}: {now}_\n"]
    if unmatched:
        lines.append(f"\n⚠️ {L['pending_specs_intro']}\n")
        for f in unmatched[:10]:
            lines.append(f"- `{f}`")
    else:
        lines.append(f"\n{L['pending_specs_none']}")
    return "\n".join(lines) + "\n"


def _build_working_agreement_reminder(L: dict[str, str]) -> str:
    """Build the Working Agreement reminder section for CONTEXT.md."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        f"## {L['working_agreement']}\n\n"
        f"_{L['auto_updated']}: {now}_\n\n"
        f"{L['wa_rule']}\n\n"
        f"{L['wa_reminder']}\n"
    )


def update_context(commits: list[dict[str, str]], L: dict[str, str]) -> bool:
    """Update CONTEXT.md with recent changes, pending specs and WA reminder."""
    f = ROOT / "CONTEXT.md"
    if not f.exists():
        return False
    content = f.read_text(encoding="utf-8")
    updated = _replace_section(content, "recent_changes", _build_recent_changes(commits, L), L)
    updated = _replace_section(updated, "pending_specs", _build_pending_specs(commits, L), L)
    updated = _replace_section(
        updated, "working_agreement", _build_working_agreement_reminder(L), L
    )
    if updated != content:
        f.write_text(updated, encoding="utf-8")
        print(f"  ✓ CONTEXT.md ({len(commits)} commits)")
        return True
    return False


# ── constitution.md ───────────────────────────────────────────────────────────

_CONSTITUTION_STUB: dict[str, str] = {
    "en": """\
# Constitution — {name}

> Immutable principles. Change these only with explicit team discussion.
> The **## Project Status** section is auto-updated. Everything else is manual.

---

## Why this project exists

_One sentence. Fill this in._

---

## Principles

### 1. Fail explicitly
When an error is detected, say exactly what happened. Never silently approve doubtful input.

### 2. Spec-driven
Every feature has a spec in `docs/specs/` written before code. The spec is the source of truth.

### 3. Quality gate is non-negotiable
`make quality` must pass before every commit. No exceptions.

---

## What this project is NOT

- ❌ _Add scope constraints here_

---

## Project Status

_Auto-updated by scripts/update_docs.py_
""",
    "es": """\
# Constitución — {name}

> Principios inmutables. Solo se cambian con discusión explícita del equipo.
> La sección **## Estado del proyecto** se auto-actualiza. Todo lo demás es manual.

---

## Por qué existe este proyecto

_Una oración. Completar esto._

---

## Principios

### 1. Fallar explícitamente
Cuando se detecta un error, decir exactamente qué pasó. Nunca aprobar input dudoso en silencio.

### 2. Spec-driven
Cada feature tiene una spec en `docs/specs/` escrita antes del código. La spec es la fuente de verdad.

### 3. El quality gate no es negociable
`make quality` debe pasar antes de cada commit. Sin excepciones.

---

## Lo que este proyecto NO es

- ❌ _Agregar restricciones de alcance aquí_

---

## Estado del proyecto

_Actualizado automáticamente por scripts/update_docs.py_
""",
}


def _build_project_status(commits: list[dict[str, str]], L: dict[str, str]) -> str:
    """Build the Project Status section for constitution.md."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = _commit_count()
    phase = L["phase_stable"] if total >= 20 else L["phase_exploratory"]
    classified = _classify_commits(commits)
    last_feat = next(
        (c["msg"] for c in commits if c["msg"].lower().startswith("feat")), "—"
    )
    lines = [
        f"## {L['project_status']}\n",
        f"_{L['auto_updated']}: {now}_\n",
        "",
        "| | |",
        "|---|---|",
        f"| **{L['phase']}** | {phase} ({total} commits total) |",
        f"| **{L['features_shipped']}** | {len(classified['features'])} (last {MAX_COMMITS} commits) |",
        f"| **{L['fixes_applied']}** | {len(classified['fixes'])} (last {MAX_COMMITS} commits) |",
        f"| **{L['last_feature']}** | {last_feat} |",
    ]
    return "\n".join(lines) + "\n"


def update_constitution(commits: list[dict[str, str]], L: dict[str, str], lang: str) -> bool:
    """Update Project Status in constitution.md. Creates stub if missing."""
    d = ROOT / "docs" / "constitution"
    f = d / "constitution.md"
    if not f.exists():
        d.mkdir(parents=True, exist_ok=True)
        stub = _CONSTITUTION_STUB.get(lang, _CONSTITUTION_STUB["en"])
        f.write_text(stub.format(name=ROOT.name), encoding="utf-8")
        print("  + Created docs/constitution/constitution.md")
    content = f.read_text(encoding="utf-8")
    updated = _replace_section(content, "project_status", _build_project_status(commits, L), L)
    if updated != content:
        f.write_text(updated, encoding="utf-8")
        print("  ✓ docs/constitution/constitution.md")
        return True
    return False


# ── clarify/assumptions.md ────────────────────────────────────────────────────

_CLARIFY_STUB: dict[str, str] = {
    "en": """\
# Assumptions & Clarifications — {name}

> What we assume, what we decided not to decide yet, and open questions.
> The **## Last Review** section is auto-updated. Everything else is manual.

---

## User assumptions

| Assumption | How we validate |
|---|---|
| Users have a stable internet connection | Known prerequisite |

---

## Technical assumptions

| Assumption | Risk if wrong |
|---|---|
| Claude API maintains current pricing | Adjust pricing model |

---

## Open questions

1. **_Question here?_**
   - Options: A | B
   - Decide when: _trigger_

---

## Consciously deferred

| Item | Reason | Reconsider when |
|---|---|---|
| Native mobile app | High cost, web sufficient for MVP | If >40% users are mobile |

---

## Last Review

_Auto-updated by scripts/update_docs.py_
""",
    "es": """\
# Supuestos y Aclaraciones — {name}

> Qué asumimos, qué decidimos no decidir aún, y preguntas abiertas.
> La sección **## Última revisión** se auto-actualiza. Todo lo demás es manual.

---

## Suposiciones sobre el usuario

| Suposición | Cómo validamos |
|---|---|
| Los usuarios tienen conexión estable | Prerequisito conocido |

---

## Suposiciones técnicas

| Suposición | Riesgo si es falsa |
|---|---|
| Claude API mantiene precios actuales | Ajustar modelo de precios |

---

## Preguntas abiertas

1. **_Pregunta aquí?_**
   - Opciones: A | B
   - Decidir cuando: _trigger_

---

## Qué se dejó fuera conscientemente

| Item | Razón | Cuándo reconsiderar |
|---|---|---|
| App móvil nativa | Costo alto, web suficiente para MVP | Si >40% usuarios son mobile |

---

## Última revisión

_Actualizado automáticamente por scripts/update_docs.py_
""",
}


def _build_last_review(clarify_file: Path, L: dict[str, str]) -> str:
    """Build the Last Review section for assumptions.md."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    stale = _commits_since_file_changed(clarify_file)
    content = clarify_file.read_text(encoding="utf-8") if clarify_file.exists() else ""
    # Count lines that end with "?" as a proxy for open questions
    open_q = sum(1 for line in content.splitlines() if line.strip().endswith("?"))

    lines = [f"## {L['last_review']}\n", f"_{L['auto_updated']}: {now}_\n"]
    if stale > 5:
        lines.append(f"\n> {L['stale_warning']} **{stale}** {L['stale_unit']}.")
    if open_q:
        lines.append(f"\n- {L['open_questions']}: **{open_q}**")
    return "\n".join(lines) + "\n"


def update_clarify(commits: list[dict[str, str]], L: dict[str, str], lang: str) -> bool:
    """Update Last Review in assumptions.md. Creates stub if missing."""
    d = ROOT / "docs" / "clarify"
    f = d / "assumptions.md"
    if not f.exists():
        d.mkdir(parents=True, exist_ok=True)
        stub = _CLARIFY_STUB.get(lang, _CLARIFY_STUB["en"])
        f.write_text(stub.format(name=ROOT.name), encoding="utf-8")
        print("  + Created docs/clarify/assumptions.md")
    content = f.read_text(encoding="utf-8")
    updated = _replace_section(content, "last_review", _build_last_review(f, L), L)
    if updated != content:
        f.write_text(updated, encoding="utf-8")
        print("  ✓ docs/clarify/assumptions.md")
        return True
    return False


# ── plan/v1-mvp.md ────────────────────────────────────────────────────────────

_PLAN_STUB: dict[str, str] = {
    "en": """\
# Technical Plan v1 — {name}

> What we build in the MVP, in what order, and the architectural decisions made.
> The **## Build Progress** section is auto-updated. Everything else is manual.

---

## MVP Scope

### Included
- [ ] _Feature 1_
- [ ] Auth
- [ ] Payments (basic)
- [ ] Admin panel (minimal)

### Consciously excluded
- _Out of scope_ — reason: _why_

---

## Build order

```
Week 1: Skeleton
├── Backend + Frontend connected
├── Auth end-to-end
└── Deploy pipeline

Week 2: Core product
└── _Core module_

Week 3: Monetization
├── Payments
└── Admin panel

Week 4: Quality
├── Critical tests
└── Observability
```

---

## Architecture Decision Records

### ADR-001: _Decision title_
**Context:** _Why this decision was needed_
**Decision:** _What was chosen_
**Consequences:** _Pros / cons_

---

## Build Progress

_Auto-updated by scripts/update_docs.py_
""",
    "es": """\
# Plan Técnico v1 — {name}

> Qué construimos en el MVP, en qué orden, y las decisiones de arquitectura tomadas.
> La sección **## Progreso de construcción** se auto-actualiza. Todo lo demás es manual.

---

## Alcance del MVP

### Incluido
- [ ] _Feature 1_
- [ ] Auth
- [ ] Pagos básicos
- [ ] Admin panel mínimo

### Excluido conscientemente
- _Out of scope_ — razón: _por qué_

---

## Orden de construcción

```
Semana 1: Esqueleto
├── Backend + Frontend conectados
├── Auth end-to-end
└── Deploy

Semana 2: Core product
└── _Módulo core_

Semana 3: Monetización
├── Pagos
└── Admin panel

Semana 4: Calidad
├── Tests críticos
└── Observabilidad
```

---

## Architecture Decision Records

### ADR-001: _Título de decisión_
**Contexto:** _Por qué se necesitó esta decisión_
**Decisión:** _Qué se eligió_
**Consecuencias:** _Pros / cons_

---

## Progreso de construcción

_Actualizado automáticamente por scripts/update_docs.py_
""",
}


def _build_build_progress(commits: list[dict[str, str]], L: dict[str, str]) -> str:
    """Build the Build Progress section for plan/v1-mvp.md."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = _commit_count()
    all_msgs = _git(["log", "--format=%s"]).splitlines()
    total_feats = sum(1 for m in all_msgs if m.lower().startswith("feat"))
    total_fixes = sum(1 for m in all_msgs if m.lower().startswith("fix"))
    last_feat = next(
        (c["msg"] for c in commits if c["msg"].lower().startswith("feat")), "—"
    )
    lines = [
        f"## {L['build_progress']}\n",
        f"_{L['auto_updated']}: {now}_\n",
        "",
        "| | |",
        "|---|---|",
        f"| **Total commits** | {total} |",
        f"| **{L['features_shipped']}** | {total_feats} (all time) |",
        f"| **{L['fixes_applied']}** | {total_fixes} (all time) |",
        f"| **{L['last_feature']}** | {last_feat} |",
    ]
    return "\n".join(lines) + "\n"


def update_plan(commits: list[dict[str, str]], L: dict[str, str], lang: str) -> bool:
    """Update Build Progress in plan/v1-mvp.md. Creates stub if missing."""
    d = ROOT / "docs" / "plan"
    f = d / "v1-mvp.md"
    if not f.exists():
        d.mkdir(parents=True, exist_ok=True)
        stub = _PLAN_STUB.get(lang, _PLAN_STUB["en"])
        f.write_text(stub.format(name=ROOT.name), encoding="utf-8")
        print("  + Created docs/plan/v1-mvp.md")
    content = f.read_text(encoding="utf-8")
    updated = _replace_section(content, "build_progress", _build_build_progress(commits, L), L)
    if updated != content:
        f.write_text(updated, encoding="utf-8")
        print("  ✓ docs/plan/v1-mvp.md")
        return True
    return False


# ── docs/specs/*.md status markers ───────────────────────────────────────────


def _spec_is_active(spec_file: Path, recent_src_files: list[str]) -> bool:
    """
    Heuristic: a spec is 'active' (in-progress) if src/ files whose name
    contains any of the spec's topic words were modified recently.
    """
    topic_words = [
        w for w in re.split(r"[-_]", spec_file.stem.lower()) if len(w) > 3
    ]
    return any(
        any(w in f.lower() for w in topic_words)
        for f in recent_src_files
        if f.startswith("src")
    )


def update_specs(commits: list[dict[str, str]]) -> int:
    """
    Update <!-- status: ... | date --> marker in each spec file.
    Returns number of specs updated.
    """
    specs_dir = ROOT / "docs" / "specs"
    if not specs_dir.exists():
        return 0

    recent_src = [f for c in commits for f in c["files"].splitlines()]
    today = datetime.now().strftime("%Y-%m-%d")
    count = 0

    for spec in specs_dir.glob("*.md"):
        if spec.name.startswith("_"):
            continue
        content = spec.read_text(encoding="utf-8")
        status = "in-progress" if _spec_is_active(spec, recent_src) else "pending"
        marker = f"<!-- status: {status} | {today} -->"
        existing = re.search(r"<!--\s*status:.*?-->", content)

        if existing:
            new_content = content[: existing.start()] + marker + content[existing.end() :]
        else:
            h1 = re.search(r"^# .+$", content, re.MULTILINE)
            if h1:
                new_content = content[: h1.end()] + f"\n{marker}" + content[h1.end() :]
            else:
                new_content = marker + "\n\n" + content

        if new_content != content:
            spec.write_text(new_content, encoding="utf-8")
            count += 1

    if count:
        print(f"  ✓ {count} spec(s) status updated")
    return count


# ── Context rotation ──────────────────────────────────────────────────────────

CONTEXT_ROTATE_LINES = 250  # rotate when CONTEXT.md exceeds this


def _load_rotate_threshold() -> int:
    """Read CONTEXT_ROTATE_LINES from .blueprint config, default 250."""
    config = ROOT / ".blueprint"
    if config.exists():
        for line in config.read_text(encoding="utf-8").splitlines():
            if line.startswith("CONTEXT_ROTATE_LINES="):
                try:
                    return int(line.split("=", 1)[1].strip())
                except ValueError:
                    pass
    return CONTEXT_ROTATE_LINES


def rotate_context() -> bool:
    """
    Archive CONTEXT.md to CONTEXT-N.md when it grows too large.
    Resets CONTEXT.md to a lean stub with a pointer to the archive.
    Returns True if rotation happened.
    """
    f = ROOT / "CONTEXT.md"
    if not f.exists():
        return False

    threshold = _load_rotate_threshold()
    lines = f.read_text(encoding="utf-8").splitlines()
    if len(lines) <= threshold:
        return False

    # Find next archive index
    n = 1
    while (ROOT / f"CONTEXT-{n}.md").exists():
        n += 1

    archive = ROOT / f"CONTEXT-{n}.md"
    archive.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")

    # Reset CONTEXT.md to lean stub
    today = datetime.now().strftime("%Y-%m-%d")
    stub = (
        f"# CONTEXT.md\n\n"
        f"> Rotated {today} — previous context archived to `CONTEXT-{n}.md`\n\n"
        f"## Current State\n\n"
        f"_Fill in the current state of the project after rotation._\n\n"
        f"## Architecture\n\n"
        f"_Key modules and their responsibilities._\n\n"
        f"## What NOT to touch\n\n"
        f"_Constraints the AI must respect._\n\n"
    )
    f.write_text(stub, encoding="utf-8")
    print(f"  ✓ CONTEXT.md rotated → CONTEXT-{n}.md ({len(lines)} lines archived)")
    return True


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    lang = _load_lang()
    L = LABELS.get(lang, LABELS["en"])

    commits = _recent_commits()
    if not commits:
        print("[docs] No commits found — nothing to update.")
        return

    print("[docs] Updating living docs...")
    results = [
        rotate_context(),
        update_context(commits, L),
        update_constitution(commits, L, lang),
        update_clarify(commits, L, lang),
        update_plan(commits, L, lang),
        bool(update_specs(commits)),
    ]
    if not any(results):
        print("  → All docs are up to date.")


if __name__ == "__main__":
    main()
