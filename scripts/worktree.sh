#!/bin/bash
# worktree.sh — physical isolation per agent + lock + registry, in one step.
#
# The collision that started all this: two agents on the same branch, one losing
# its place while the other moved. Worktrees fix it physically — each agent gets
# its own checkout on its own branch. This wraps `git worktree` so that creating
# one also acquires the module lock (shared, in locks.json) and registers the
# agent locally (registry.local.yaml). Ending releases both.
#
# Usage:
#   bash scripts/worktree.sh start <module> [branch] [holder]
#   bash scripts/worktree.sh end   <module>
#   bash scripts/worktree.sh list
#
# holder defaults to $DCDD_AGENT or git user.name.

set -e

ROOT="$(git rev-parse --show-toplevel)"
LOCKS="$ROOT/.context/locks.json"
REGISTRY="$ROOT/.context/agents/registry.local.yaml"
CMD="${1:-list}"
MODULE="$2"
BRANCH="${3:-feature/$MODULE}"
HOLDER="${4:-${DCDD_AGENT:-$(git config user.name)}}"
NOW="$(python3 -c 'import datetime;print(datetime.datetime.now(datetime.timezone.utc).isoformat())')"
WORKTREE=".worktrees/$MODULE"

ensure_files() {
  mkdir -p "$ROOT/.context/agents"
  [ -f "$LOCKS" ] || echo '{"locks": []}' > "$LOCKS"
  [ -f "$REGISTRY" ] || printf 'agents:\n' > "$REGISTRY"
}

lock_add() {
  python3 - "$LOCKS" "$MODULE" "$HOLDER" "$BRANCH" "$WORKTREE" "$NOW" <<'PY'
import json, sys
path, module, holder, branch, wt, now = sys.argv[1:7]
data = json.load(open(path))
for l in data["locks"]:
    if l["module"] == module and l["holder"] != holder:
        sys.exit(f"🚫 module '{module}' already locked by '{l['holder']}'. Coordinate first.")
data["locks"] = [l for l in data["locks"] if l["module"] != module]
data["locks"].append({"module": module, "holder": holder, "branch": branch,
                      "worktree": wt, "acquired_at": now, "ttl_minutes": 240})
json.dump(data, open(path, "w"), indent=2)
PY
}

lock_remove() {
  python3 - "$LOCKS" "$MODULE" <<'PY'
import json, sys
path, module = sys.argv[1:3]
data = json.load(open(path))
data["locks"] = [l for l in data["locks"] if l["module"] != module]
json.dump(data, open(path, "w"), indent=2)
PY
}

registry_add() {
  cat >> "$REGISTRY" <<EOF
  - id: "$HOLDER"
    module: "$MODULE"
    worktree: "$WORKTREE"
    started_at: "$NOW"
EOF
}

registry_remove() {
  python3 - "$REGISTRY" "$MODULE" <<'PY'
import sys
path, module = sys.argv[1:3]
lines = open(path).read().splitlines()
out, skip = [], False
for line in lines:
    if line.strip().startswith("- id:"):
        skip = False
    if f'module: "{module}"' in line:
        # drop the 4-line block: walk back to its "- id:" and forward to next
        while out and not out[-1].strip().startswith("- id:"):
            out.pop()
        if out:
            out.pop()
        skip = True
        continue
    if skip and (line.startswith("    ") or not line.strip()):
        continue
    skip = False
    out.append(line)
open(path, "w").write("\n".join(out) + "\n")
PY
}

case "$CMD" in
  start)
    [ -z "$MODULE" ] && { echo "usage: worktree.sh start <module> [branch] [holder]"; exit 1; }
    ensure_files
    lock_add
    git worktree add -b "$BRANCH" "$WORKTREE" 2>/dev/null || git worktree add "$WORKTREE" "$BRANCH"
    registry_add
    echo "✓ worktree '$WORKTREE' on branch '$BRANCH' — locked for '$HOLDER'"
    echo "  cd $WORKTREE && export DCDD_AGENT='$HOLDER'"
    ;;
  end)
    [ -z "$MODULE" ] && { echo "usage: worktree.sh end <module>"; exit 1; }
    ensure_files
    git worktree remove "$WORKTREE" --force 2>/dev/null || true
    lock_remove
    registry_remove
    echo "✓ released '$MODULE' — worktree removed, lock freed"
    ;;
  list)
    ensure_files
    echo "── Active locks (shared) ──"
    python3 -c "import json;[print(f\"  {l['module']:20} {l['holder']:15} {l['branch']}\") for l in json.load(open('$LOCKS'))['locks']] or print('  (none)')"
    echo ""
    echo "── git worktrees ──"
    git worktree list
    ;;
  *)
    echo "usage: worktree.sh {start <module> [branch] [holder] | end <module> | list}"
    exit 1
    ;;
esac
