#!/usr/bin/env python3
"""scope_guard.py — the DCDD coordination layer enforcement.

Where semantic_validator checks that changes don't *contradict* each other,
scope_guard checks that changes are *allowed in the first place*:

    1. Scope   — every changed file is inside the active task's `allowed`
                 globs and outside its `forbidden` globs.
    2. Locks   — no changed file belongs to a module another holder has locked
                 (respecting ttl_minutes; stale locks are ignored).

This is the leash. It's what would have stopped the agent that "fixed"
Cache-Control and build scripts nobody asked it to touch: those files are in
the task's `forbidden` list, so the push is blocked with a clear reason.

Identity ("who am I") comes from the DCDD_AGENT env var, falling back to the
git user name. A lock held by *you* never blocks you.

Runs in the pre-push hook (local) alongside the semantic validator.

Usage:
    python3 scripts/scope_guard.py
    python3 scripts/scope_guard.py --task .context/tasks/pricing.yaml
    python3 scripts/scope_guard.py --changed src/a.ts --base origin/main
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from semantic_validator import load_yaml, _as_list, _repo_files  # noqa: E402


def changed_files(base: str) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", base], text=True, stderr=subprocess.DEVNULL
        )
        return [l for l in out.splitlines() if l.strip()]
    except subprocess.CalledProcessError:
        return []


def whoami(root: str) -> str:
    if os.environ.get("DCDD_AGENT"):
        return os.environ["DCDD_AGENT"]
    try:
        return subprocess.check_output(
            ["git", "config", "user.name"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def find_task(root: str, explicit: str | None) -> dict | None:
    path = explicit or os.environ.get("DCDD_TASK")
    if not path:
        tasks_dir = os.path.join(root, ".context", "tasks")
        candidates = []
        if os.path.isdir(tasks_dir):
            candidates = [
                os.path.join(tasks_dir, f)
                for f in os.listdir(tasks_dir)
                if f.endswith(".yaml") and not f.startswith("_")
            ]
        if len(candidates) == 1:
            path = candidates[0]
    if path and os.path.exists(path):
        return load_yaml(path)
    return None


def check_scope(task: dict, files: list[str]) -> list[str]:
    errors = []
    allowed = _as_list(task.get("allowed"))
    forbidden = _as_list(task.get("forbidden"))
    for f in files:
        if any(fnmatch.fnmatch(f, g) for g in forbidden):
            errors.append(f"'{f}' is FORBIDDEN by task '{task.get('id')}' — "
                          f"infra change needs its own task")
        elif allowed and not any(fnmatch.fnmatch(f, g) for g in allowed):
            errors.append(f"'{f}' is outside task '{task.get('id')}' scope "
                          f"(not in `allowed`)")
    return errors


def _module_of(root: str, path: str) -> str | None:
    base = os.path.join(root, "docs", "modular")
    for dp, _, names in os.walk(base):
        if "module.yaml" in names:
            data = load_yaml(os.path.join(dp, "module.yaml"))
            owns = _as_list(data.get("owns"))
            if any(fnmatch.fnmatch(path, g) for g in owns):
                return data.get("module") or os.path.basename(dp)
    return None


def _active_locks(root: str) -> list[dict]:
    path = os.path.join(root, ".context", "locks.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    now = dt.datetime.now(dt.timezone.utc)
    live = []
    for lock in data.get("locks", []):
        ts = lock.get("acquired_at", "")
        ttl = int(lock.get("ttl_minutes", 240))
        try:
            acquired = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if (now - acquired).total_seconds() <= ttl * 60:
                live.append(lock)
        except ValueError:
            live.append(lock)  # unparseable timestamp → treat as active, fail safe
    return live


def check_locks(root: str, files: list[str], me: str) -> list[str]:
    locks = _active_locks(root)
    if not locks:
        return []
    held = {lock["module"]: lock for lock in locks}
    errors, flagged = [], set()
    for f in files:
        mod = _module_of(root, f)
        if mod in held and held[mod].get("holder") != me and mod not in flagged:
            flagged.add(mod)
            errors.append(f"module '{mod}' is locked by "
                          f"'{held[mod].get('holder')}' — coordinate before editing")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="DCDD scope & lock guard")
    ap.add_argument("--root", default=".")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--task")
    ap.add_argument("--changed", nargs="*")
    args = ap.parse_args()

    files = args.changed if args.changed is not None else changed_files(args.base)
    if not files:
        print("✓ scope guard: no changed files.")
        return 0

    errors, warnings = [], []
    task = find_task(args.root, args.task)
    if task:
        errors += check_scope(task, files)
    else:
        warnings.append("no active task in .context/tasks/ — scope check skipped")

    errors += check_locks(args.root, files, whoami(args.root))

    for w in warnings:
        print(f"  ⚠ {w}")
    for e in errors:
        print(f"  ✗ {e}")

    if errors:
        print(f"\n🚫 Scope guard FAILED: {len(errors)} violation(s).")
        print("   Out of scope on purpose? git push --no-verify")
        return 1
    print(f"\n✓ Scope guard passed: {len(files)} file(s) in scope.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
