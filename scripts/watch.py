#!/usr/bin/env python3
"""
watch.py — Optional file watcher that runs update_docs.py when the project changes.

Use this as a fallback when your AI agent doesn't support session-end hooks.
Watches src/, docs/specs/, and CONTEXT.md for changes and auto-updates living docs.

Usage:
    python3 scripts/watch.py          # watch in foreground
    python3 scripts/watch.py &        # watch in background
    python3 scripts/watch.py --help

Requirements:
    pip install watchdog
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
WATCH_DIRS = ["src", "docs/specs"]
WATCH_FILES = ["CONTEXT.md"]
DEBOUNCE_SECONDS = 3


def _run_update() -> None:
    script = ROOT / "scripts" / "update_docs.py"
    if not script.exists():
        return
    subprocess.run([sys.executable, str(script)], cwd=ROOT)


def _watch_with_watchdog() -> None:
    from watchdog.events import FileSystemEventHandler  # type: ignore[import]
    from watchdog.observers import Observer  # type: ignore[import]

    last_run = 0.0

    class Handler(FileSystemEventHandler):
        def on_any_event(self, event):  # type: ignore[override]
            nonlocal last_run
            if event.is_directory:
                return
            now = time.time()
            if now - last_run < DEBOUNCE_SECONDS:
                return
            last_run = now
            print(f"[watch] change detected — running update_docs.py")
            _run_update()

    observer = Observer()
    handler = Handler()

    for d in WATCH_DIRS:
        target = ROOT / d
        if target.exists():
            observer.schedule(handler, str(target), recursive=True)

    for f in WATCH_FILES:
        target = ROOT / f
        if target.exists():
            observer.schedule(handler, str(target.parent), recursive=False)

    observer.start()
    print(f"[watch] watching {ROOT} — Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def _watch_polling() -> None:
    """Fallback polling watcher when watchdog is not installed."""
    targets = [ROOT / d for d in WATCH_DIRS if (ROOT / d).exists()]
    targets += [ROOT / f for f in WATCH_FILES if (ROOT / f).exists()]

    def snapshot() -> dict[str, float]:
        state: dict[str, float] = {}
        for t in targets:
            if t.is_dir():
                for p in t.rglob("*"):
                    if p.is_file():
                        try:
                            state[str(p)] = p.stat().st_mtime
                        except OSError:
                            pass
            elif t.is_file():
                try:
                    state[str(t)] = t.stat().st_mtime
                except OSError:
                    pass
        return state

    prev = snapshot()
    print(f"[watch] polling {ROOT} every {DEBOUNCE_SECONDS}s — Ctrl+C to stop")
    try:
        while True:
            time.sleep(DEBOUNCE_SECONDS)
            curr = snapshot()
            if curr != prev:
                print("[watch] change detected — running update_docs.py")
                _run_update()
                prev = curr
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    try:
        import watchdog  # noqa: F401
        _watch_with_watchdog()
    except ImportError:
        print("[watch] watchdog not installed — using polling (pip install watchdog for better performance)")
        _watch_polling()
