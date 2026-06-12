#!/bin/bash
# install_hooks.sh — Install git hooks for this project.
# Run once after cloning: bash scripts/install_hooks.sh

set -e

HOOKS_DIR="$(git rev-parse --git-dir)/hooks"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"

echo "Installing git hooks in $HOOKS_DIR"

# ── pre-commit: warn when src/ changes without a spec ────────────────────────
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Warn when src/ files are staged without a corresponding spec in docs/specs/.

STAGED_SRC=$(git diff --cached --name-only | grep "^src/" | grep -v "\.pyc$" || true)
if [ -z "$STAGED_SRC" ]; then
  exit 0
fi

SPECS_DIR="docs/specs"
if [ ! -d "$SPECS_DIR" ]; then
  exit 0
fi

SPEC_WORDS=$(ls "$SPECS_DIR"/*.md 2>/dev/null | xargs -I{} basename {} .md | tr '-_' '\n' | awk 'length>3' | sort -u)
UNMATCHED=""

for f in $STAGED_SRC; do
  FNAME=$(basename "$f" | tr '[:upper:]' '[:lower:]')
  MATCHED=0
  for word in $SPEC_WORDS; do
    if echo "$FNAME" | grep -q "$word"; then
      MATCHED=1
      break
    fi
  done
  if [ "$MATCHED" -eq 0 ]; then
    UNMATCHED="$UNMATCHED\n  - $f"
  fi
done

if [ -n "$UNMATCHED" ]; then
  echo ""
  echo "🚫 WORKING AGREEMENT VIOLATION — commit blocked."
  echo ""
  echo "  src/ changed without a spec in docs/specs/ for:"
  echo -e "$UNMATCHED"
  echo ""
  echo "  Fix: write a spec in docs/specs/<name>.md first, then commit."
  echo "  Cosmetic change? Use: git commit --no-verify"
  echo ""
  exit 1
fi

exit 0
EOF

chmod +x "$HOOKS_DIR/pre-commit"
echo "  ✓ pre-commit installed (spec check)"

# ── post-commit: update all living docs after every commit ────────────────────
cat > "$HOOKS_DIR/post-commit" << EOF
#!/bin/bash
# Auto-updates CONTEXT.md, constitution, clarify, plan and spec statuses
python3 "$SCRIPTS_DIR/update_docs.py" 2>&1 | tee -a "$ROOT_DIR/.blueprint-log" || true
EOF

chmod +x "$HOOKS_DIR/post-commit"
echo "  ✓ post-commit installed (living docs)"

# ── pre-push: DCDD semantic + scope gate (local mirror of the central CI) ─────
cat > "$HOOKS_DIR/pre-push" << EOF
#!/bin/bash
# Local mirror of the central gate. Same engine, smaller scope. What passes here
# passes in CI. Bypass a false positive with: git push --no-verify
ROOT="\$(git rev-parse --show-toplevel)"
BASE="\${DCDD_BASE:-origin/main}"
FAIL=0

if [ -f "\$ROOT/scripts/scope_guard.py" ]; then
  echo "▸ DCDD scope guard..."
  python3 "\$ROOT/scripts/scope_guard.py" --root "\$ROOT" --base "\$BASE" || FAIL=1
fi

if [ -f "\$ROOT/scripts/semantic_validator.py" ]; then
  echo "▸ DCDD semantic validator (local)..."
  python3 "\$ROOT/scripts/semantic_validator.py" --mode local --root "\$ROOT" --base "\$BASE" || FAIL=1
fi

exit \$FAIL
EOF

chmod +x "$HOOKS_DIR/pre-push"
echo "  ✓ pre-push installed (semantic + scope gate)"

echo ""
echo "Done. Hooks active:"
echo "  pre-commit  → warns when src/ changes have no spec"
echo "  post-commit → auto-updates all living docs"
echo "  pre-push    → DCDD semantic validator + scope guard (local gate)"
echo ""
echo "To update docs manually:    python3 scripts/update_docs.py"
echo "To validate semantics:      python3 scripts/semantic_validator.py --mode central"
echo "Hook log: .blueprint-log"
