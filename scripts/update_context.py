#!/usr/bin/env python3
"""
Updates CONTEXT.md with:
  - Recent git commits in '## Últimos cambios'
  - Spec file list in '## Specs disponibles'
  - New/modified files summary in '## Archivos modificados recientemente'
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONTEXT_FILE = ROOT / "CONTEXT.md"
SPECS_DIR = ROOT / "specs"
MAX_COMMITS = 10


# ── Helpers ──────────────────────────────────────────────────────────────────

def _git(*args: str) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    return r.stdout.strip() if r.returncode == 0 else ""


def _replace_section(content: str, marker: str, new_body: str) -> str:
    """Replace everything from `marker` to the next `## ` heading (or EOF)."""
    if marker not in content:
        return content + f"\n{marker}\n{new_body}\n"

    start = content.index(marker)
    # Find the next H2 after the marker
    rest = content[start + len(marker):]
    next_h2 = rest.find("\n## ", 1)
    if next_h2 == -1:
        return content[:start] + marker + "\n" + new_body + "\n"
    return content[:start] + marker + "\n" + new_body + "\n" + rest[next_h2 + 1:]


# ── Section builders ─────────────────────────────────────────────────────────

def build_commits_section() -> str:
    raw = _git("log", f"-{MAX_COMMITS}", "--pretty=format:%ad %s", "--date=short")
    if not raw:
        return ""
    lines = [f"- [{c[:10]}] {c[11:]}" for c in raw.split("\n") if c]
    return "<!-- Actualizado automáticamente por scripts/update_context.py -->\n" + "\n".join(lines)


def build_specs_section() -> str:
    if not SPECS_DIR.exists():
        return ""
    rows = ["| Feature | Archivo |", "|---|---|"]
    for spec in sorted(SPECS_DIR.glob("*.md")):
        # Extract first H1 line as feature name
        first_line = ""
        for line in spec.read_text().splitlines():
            if line.startswith("# "):
                first_line = line[2:].strip()
                break
        name = first_line or spec.stem.replace("-", " ").title()
        rows.append(f"| {name} | `specs/{spec.name}` |")
    return "\n".join(rows)


def build_recent_files_section() -> str:
    """List files changed in the last 3 commits, grouped by area."""
    raw = _git("diff", "--name-only", "HEAD~3", "HEAD")
    if not raw:
        raw = _git("diff", "--name-only", "HEAD~1", "HEAD")
    if not raw:
        return ""
    files = [f for f in raw.split("\n") if f]
    if not files:
        return ""
    lines = [f"- `{f}`" for f in sorted(files)[:20]]
    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def update_context() -> None:
    content = CONTEXT_FILE.read_text()

    commits = build_commits_section()
    if commits:
        content = _replace_section(content, "## Últimos cambios", commits)

    specs = build_specs_section()
    if specs:
        content = _replace_section(content, "## Specs disponibles", specs)

    CONTEXT_FILE.write_text(content)
    print(f"✓ CONTEXT.md actualizado ({MAX_COMMITS} commits, {len(list(SPECS_DIR.glob('*.md')))} specs)")


if __name__ == "__main__":
    update_context()
