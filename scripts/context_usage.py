#!/usr/bin/env python3
"""
context_usage.py — Estimates current Claude Code session context usage.

Reads the active session JSONL and calculates token consumption,
replicating what /context shows in the UI.

Usage:
    python3 scripts/context_usage.py
    python3 scripts/context_usage.py --watch   # check every 60s
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# ── Model context limits ──────────────────────────────────────────────────────
MODEL_LIMITS: dict[str, int] = {
    "claude-opus-4":      200_000,
    "claude-sonnet-4-6":  200_000,
    "claude-sonnet-4-5":  200_000,
    "claude-haiku-4-5":   200_000,
    "claude-opus-3-5":    200_000,
    "claude-sonnet-3-5":  200_000,
    "claude-haiku-3-5":   200_000,
}
DEFAULT_LIMIT = 200_000

# Fixed overhead (system prompt + tools + skills + autocompact buffer)
FIXED_OVERHEAD = 50_000

# Warning thresholds
WARN_YELLOW = 0.20   # ≤ 20% free → warning
WARN_RED    = 0.10   # ≤ 10% free → critical


def _find_active_session() -> tuple[str, Path] | None:
    """Find the most recently modified JSONL across all projects — that's the active session."""
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return None

    all_jsonl = [
        f for f in projects_dir.rglob("*.jsonl")
        if "subagents" not in f.parts
    ]
    if not all_jsonl:
        return None

    latest = max(all_jsonl, key=lambda p: p.stat().st_mtime)
    return latest.stem, latest


def _calculate_usage(jsonl: Path) -> dict:
    """Parse JSONL — count messages only after the last compact_boundary.

    cache_read_input_tokens from the last assistant message reflects what
    the model actually read in that turn = best proxy for context window usage.
    """
    lines = jsonl.read_text().splitlines()

    # Find index of last compact_boundary
    last_compact_idx = -1
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if obj.get("type") == "system" and obj.get("subtype") == "compact_boundary":
                last_compact_idx = i
        except json.JSONDecodeError:
            continue

    # Only process messages after last compact
    active_lines = lines[last_compact_idx + 1:] if last_compact_idx >= 0 else lines

    message_count = 0
    model = "claude-sonnet-4-6"
    last_cache_read = 0
    last_input = 0
    last_output = 0

    for line in active_lines:
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        if obj.get("type") != "assistant":
            continue

        msg = obj.get("message", {})
        if not isinstance(msg, dict):
            continue

        if "model" in msg:
            model = msg["model"]

        usage = msg.get("usage")
        if not usage:
            continue

        message_count += 1
        last_cache_read = usage.get("cache_read_input_tokens", 0)
        last_input      = usage.get("input_tokens", 0)
        last_output     = usage.get("output_tokens", 0)

    return {
        "model": model,
        "cache_read": last_cache_read,
        "last_input": last_input,
        "last_output": last_output,
        "message_count": message_count,
    }


def _format_k(n: int) -> str:
    return f"{n/1000:.1f}k"


def _bar(pct: float, width: int = 40) -> str:
    filled = int(pct * width)
    return "█" * filled + "░" * (width - filled)


def report(jsonl: Path) -> float:
    """Print context usage report. Returns free_pct."""
    usage = _calculate_usage(jsonl)
    model = usage["model"]
    limit = MODEL_LIMITS.get(model, DEFAULT_LIMIT)

    # cache_read reflects what the model actually read in the last turn
    messages_tokens = usage["cache_read"]
    total_used = min(messages_tokens + FIXED_OVERHEAD, limit)
    free = max(0, limit - total_used)
    used_pct = total_used / limit
    free_pct = free / limit

    # Status
    if free_pct <= WARN_RED:
        status = "🔴 CRÍTICO"
        action = "Ejecuta /handoff-save AHORA → abre sesión nueva → /handoff-open"
    elif free_pct <= WARN_YELLOW:
        status = "⚠️  ADVERTENCIA"
        action = "Ejecuta /handoff-save pronto antes de continuar"
    else:
        status = "✅ OK"
        action = "Puedes seguir trabajando"

    print(f"\n{'─'*52}")
    print(f"  Context Usage — {model}")
    print(f"{'─'*52}")
    print(f"  {_format_k(total_used)} / {_format_k(limit)} tokens ({used_pct*100:.0f}%)")
    print(f"  [{_bar(used_pct, 40)}]")
    print()
    print(f"  {'Messages':<22} {_format_k(messages_tokens):>8}  {messages_tokens/limit*100:>5.1f}%")
    print(f"  {'Fixed overhead':<22} {_format_k(FIXED_OVERHEAD):>8}  {FIXED_OVERHEAD/limit*100:>5.1f}%")
    print(f"  {'Free space':<22} {_format_k(free):>8}  {free_pct*100:>5.1f}%")
    print()
    print(f"  Turnos en sesión: {usage['message_count']}")
    if usage['message_count'] > 0:
        tokens_per_turn = messages_tokens / usage['message_count']
        turns_left = int(free / tokens_per_turn) if tokens_per_turn > 0 else 0
        print(f"  ~{tokens_per_turn:.0f} tokens/turno → ~{turns_left} turnos restantes")
    print()
    print(f"  {status} — {action}")
    print(f"{'─'*52}\n")

    return free_pct


def main() -> None:
    watch_mode = "--watch" in sys.argv

    result = _find_active_session()
    if not result:
        print("❌ No se encontró sesión activa de Claude Code.")
        sys.exit(1)

    session_id, jsonl = result

    if watch_mode:
        print(f"[context_usage] watching session {session_id[:8]}... (Ctrl+C to stop)")
        try:
            while True:
                free_pct = report(jsonl)
                interval = 30 if free_pct <= WARN_YELLOW else 60
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nDetenido.")
    else:
        report(jsonl)


if __name__ == "__main__":
    main()
