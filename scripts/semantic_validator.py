#!/usr/bin/env python3
"""semantic_validator.py — the DCDD semantic layer.

ONE engine, two modes. Reads every docs/modular/*/module.yaml, builds a
dependency graph, and verifies the changes are semantically consistent —
something tests and linters never check.

    local   (pre-push hook):  validate changed modules + their consumers.
    central (CI before merge): validate the whole graph, cross-checked.

Same code in both. The only difference is scope, so the feedback a dev gets
locally predicts exactly what the central gate will say.

Checks:
    1. consumes resolution — every symbol a module consumes must still be in
       the provider's `provides`. (Catches: turismo drops getCafeProfile while
       core still consumes it. Code compiles, tests pass, this fails.)
    2. ownership conflict — no file may be owned by two modules.
    3. invariant resolution — every referenced invariant id exists in the
       constitution.
    4. provides drift (warn) — declared public symbols should appear in the
       module's own code.

Zero dependencies: ships its own minimal YAML reader for the module.yaml
subset, so it runs anywhere python3 runs — no pip, honoring the no-lock-in rule.

Usage:
    python3 scripts/semantic_validator.py --mode central
    python3 scripts/semantic_validator.py --mode local
    python3 scripts/semantic_validator.py --mode local --changed src/a.ts src/b.ts
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import sys
from dataclasses import dataclass, field

# ── Minimal YAML reader ──────────────────────────────────────────────────────
# Supports exactly the module.yaml subset: nested maps, block sequences of
# scalars, block sequences of maps, inline flow lists [a, b], quoted/bare
# scalars, and comments. Not a general YAML parser — intentionally small.


def _strip_comment(line: str) -> str:
    """Remove a trailing # comment that is not inside quotes."""
    out, quote = [], None
    for ch in line:
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#":
            break
        out.append(ch)
    return "".join(out)


def _scalar(token: str):
    token = token.strip()
    if not token:
        return None
    if token[0] in "\"'" and token[-1] == token[0]:
        return token[1:-1]
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        return [_scalar(t) for t in inner.split(",")] if inner else []
    return token


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_block(lines: list[str], i: int, indent: int):
    """Parse a map or sequence at the given indent. Returns (value, next_i)."""
    # Sequence?
    if i < len(lines) and _indent(lines[i]) == indent and lines[i].lstrip().startswith("- "):
        return _parse_seq(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_seq(lines: list[str], i: int, indent: int):
    items = []
    while i < len(lines):
        if _indent(lines[i]) != indent or not lines[i].lstrip().startswith("- "):
            break
        rest = lines[i].lstrip()[2:]
        if ":" in rest and not rest.strip().startswith("["):
            # Sequence of maps — re-expand "- key: val" as a map at indent+2.
            lines[i] = " " * (indent + 2) + rest
            value, i = _parse_map(lines, i, indent + 2)
            items.append(value)
        else:
            items.append(_scalar(rest))
            i += 1
    return items, i


def _parse_map(lines: list[str], i: int, indent: int):
    result = {}
    while i < len(lines):
        if _indent(lines[i]) != indent:
            break
        key, _, val = lines[i].partition(":")
        key = key.strip()
        i += 1
        if val.strip():
            result[key] = _scalar(val)
        else:
            child, i = _parse_block(lines, i, indent + 2)
            result[key] = child
    return result, i


def load_yaml(path: str) -> dict:
    raw = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = _strip_comment(line.rstrip("\n"))
            if line.strip():
                raw.append(line)
    value, _ = _parse_block(raw, 0, 0)
    return value or {}


# ── Domain model ──────────────────────────────────────────────────────────────
@dataclass
class Module:
    name: str
    path: str
    owner: str = ""
    owns: list[str] = field(default_factory=list)
    provides: list[dict] = field(default_factory=list)
    consumes: list[dict] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)

    @property
    def provided_names(self) -> set[str]:
        return {p["name"] for p in self.provides if isinstance(p, dict) and "name" in p}


def _as_list(v) -> list:
    return v if isinstance(v, list) else ([] if v is None else [v])


def load_modules(root: str) -> dict[str, Module]:
    modules: dict[str, Module] = {}
    base = os.path.join(root, "docs", "modular")
    for dirpath, _, files in os.walk(base):
        if "module.yaml" not in files:
            continue
        data = load_yaml(os.path.join(dirpath, "module.yaml"))
        name = data.get("module") or os.path.basename(dirpath)
        modules[name] = Module(
            name=name,
            path=dirpath,
            owner=data.get("owner", ""),
            owns=_as_list(data.get("owns")),
            provides=_as_list(data.get("provides")),
            consumes=_as_list(data.get("consumes")),
            invariants=_as_list(data.get("invariants")),
        )
    return modules


# ── Checks ────────────────────────────────────────────────────────────────────
@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)


def check_consumes(modules: dict[str, Module], scope: set[str], rep: Report):
    for name in scope:
        mod = modules[name]
        for dep in mod.consumes:
            if not isinstance(dep, dict):
                continue
            target = dep.get("module")
            if target not in modules:
                rep.error(f"{name}: consumes unknown module '{target}'")
                continue
            available = modules[target].provided_names
            for sym in _as_list(dep.get("symbols")):
                if sym not in available:
                    rep.error(
                        f"{name}: consumes '{target}.{sym}' but '{target}' "
                        f"no longer provides it (broken contract)"
                    )


def check_ownership(modules: dict[str, Module], root: str, rep: Report):
    owners: dict[str, str] = {}
    for path in _repo_files(root):
        for mod in modules.values():
            if any(fnmatch.fnmatch(path, g) for g in mod.owns):
                if path in owners and owners[path] != mod.name:
                    rep.error(
                        f"ownership conflict: '{path}' claimed by "
                        f"'{owners[path]}' and '{mod.name}'"
                    )
                owners[path] = mod.name


def check_invariants(modules: dict[str, Module], scope: set[str], root: str, rep: Report):
    constitution = os.path.join(root, "docs", "constitution", "constitution.md")
    text = ""
    if os.path.exists(constitution):
        with open(constitution, encoding="utf-8") as fh:
            text = fh.read()
    for name in scope:
        for inv in modules[name].invariants:
            if inv and inv not in text:
                rep.error(f"{name}: invariant '{inv}' not found in constitution")


def check_drift(modules: dict[str, Module], scope: set[str], root: str, rep: Report):
    for name in scope:
        mod = modules[name]
        owned = [f for f in _repo_files(root) if any(fnmatch.fnmatch(f, g) for g in mod.owns)]
        blob = ""
        for f in owned:
            try:
                with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
                    blob += fh.read()
            except OSError:
                pass
        for sym in mod.provided_names:
            if sym and sym not in blob:
                rep.warn(f"{name}: declares provides '{sym}' but it is not found in owned code")


# ── Scope resolution ──────────────────────────────────────────────────────────
def _repo_files(root: str) -> list[str]:
    skip = {".git", "node_modules", ".venv", "__pycache__", ".svelte-kit", "dist", "build"}
    out = []
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            rel = os.path.relpath(os.path.join(dp, f), root)
            out.append(rel)
    return out


def modules_for_files(modules: dict[str, Module], files: list[str]) -> set[str]:
    hit = set()
    for f in files:
        for mod in modules.values():
            if any(fnmatch.fnmatch(f, g) for g in mod.owns):
                hit.add(mod.name)
    return hit


def consumers_of(modules: dict[str, Module], targets: set[str]) -> set[str]:
    out = set()
    for mod in modules.values():
        for dep in mod.consumes:
            if isinstance(dep, dict) and dep.get("module") in targets:
                out.add(mod.name)
    return out


def changed_files(base: str) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", base], text=True, stderr=subprocess.DEVNULL
        )
        return [l for l in out.splitlines() if l.strip()]
    except subprocess.CalledProcessError:
        return []


# ── Orchestration ─────────────────────────────────────────────────────────────
def run(mode: str, root: str, changed: list[str] | None, base: str) -> Report:
    modules = load_modules(root)
    rep = Report()
    if not modules:
        rep.warn("no module.yaml found under docs/modular/ — nothing to validate")
        return rep

    if mode == "central":
        scope = set(modules)
        check_ownership(modules, root, rep)
    else:
        files = changed if changed is not None else changed_files(base)
        touched = modules_for_files(modules, files)
        scope = touched | consumers_of(modules, touched)
        if not scope:
            return rep

    check_consumes(modules, scope, rep)
    check_invariants(modules, scope, root, rep)
    check_drift(modules, scope, root, rep)
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description="DCDD semantic validator")
    ap.add_argument("--mode", choices=["local", "central"], default="local")
    ap.add_argument("--root", default=".")
    ap.add_argument("--base", default="origin/main", help="git ref for local diff")
    ap.add_argument("--changed", nargs="*", help="explicit changed files (local mode)")
    args = ap.parse_args()

    rep = run(args.mode, args.root, args.changed, args.base)

    for w in rep.warnings:
        print(f"  ⚠ {w}")
    for e in rep.errors:
        print(f"  ✗ {e}")

    if rep.errors:
        print(f"\n🚫 Semantic validation FAILED ({args.mode}): "
              f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s).")
        return 1
    print(f"\n✓ Semantic validation passed ({args.mode}): "
          f"{len(rep.warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
