#!/bin/bash
# setup.sh — Create a new project from the AI App Blueprint v2
#
# Usage:
#   bash scripts/setup.sh <project-name>              (English, default)
#   bash scripts/setup.sh <project-name> --lang es    (Spanish)
#
# What it does:
#   1. Creates project directory with full doc structure
#   2. Installs git hooks (post-commit + Claude Code Stop)
#   3. Creates .blueprint config file
#   4. Copies all templates and renames placeholders

set -e

PROJECT_NAME="${1:-my-app}"
LANG_FLAG="en"

# Parse --lang flag
for arg in "$@"; do
  case $arg in
    --lang) shift ;;
    es|ES) LANG_FLAG="es" ;;
    en|EN) LANG_FLAG="en" ;;
  esac
done
# Also check second argument directly
if [ "$2" = "--lang" ] && [ -n "$3" ]; then
  LANG_FLAG="$3"
elif [ "$2" = "es" ] || [ "$2" = "--lang=es" ]; then
  LANG_FLAG="es"
fi

BLUEPRINT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_DIR="$(pwd)/$PROJECT_NAME"

echo "Bootstrapping $PROJECT_NAME (lang: $LANG_FLAG)..."

# ── Create project directory ───────────────────────────────────────────────────
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"
git init

# ── Copy blueprint files ───────────────────────────────────────────────────────
cp -r "$BLUEPRINT_DIR/blueprint/." .
mkdir -p scripts
cp "$BLUEPRINT_DIR/scripts/update_docs.py" scripts/
cp "$BLUEPRINT_DIR/scripts/install_hooks.sh" scripts/
# DCDD v2 — semantic layer + coordination
cp "$BLUEPRINT_DIR/scripts/semantic_validator.py" scripts/
cp "$BLUEPRINT_DIR/scripts/scope_guard.py" scripts/
cp "$BLUEPRINT_DIR/scripts/worktree.sh" scripts/
mkdir -p .github/workflows
cp "$BLUEPRINT_DIR/github/workflows/ci.yml" .github/workflows/
cp "$BLUEPRINT_DIR/github/workflows/semantic-validation.yml" .github/workflows/
cp "$BLUEPRINT_DIR/github/PULL_REQUEST_TEMPLATE.md" .github/

# DCDD v2 — coordination scaffolding (.context/)
mkdir -p .context/agents .context/tasks
cp "$BLUEPRINT_DIR/blueprint/.context/locks.json.template" .context/locks.json.template
cp "$BLUEPRINT_DIR/blueprint/.context/agents/registry.local.yaml.template" .context/agents/
cp "$BLUEPRINT_DIR/blueprint/.context/tasks/_task.template.yaml" .context/tasks/
cp "$BLUEPRINT_DIR/blueprint/docs/modular/_module.template.yaml" docs/modular/ 2>/dev/null || true
# locks.json starts empty (committed); registry/tasks are created per-session
echo '{"locks": []}' > .context/locks.json

# ── Rename templates ───────────────────────────────────────────────────────────
mv CONTEXT.md.template CONTEXT.md 2>/dev/null || true
mv CLAUDE.md.template CLAUDE.md 2>/dev/null || true
mv WORKING-AGREEMENT.md.template WORKING-AGREEMENT.md 2>/dev/null || true
mv .env.example.template .env.example 2>/dev/null || true
mv Makefile.template Makefile 2>/dev/null || true

# ── Replace placeholders ───────────────────────────────────────────────────────
DATE=$(date +%Y-%m-%d)
find . -name "*.md" -not -path "./.git/*" | xargs sed -i '' \
  "s/{{PROJECT_NAME}}/$PROJECT_NAME/g; s/{{DATE}}/$DATE/g" 2>/dev/null || true

# ── Create base directory structure ───────────────────────────────────────────
mkdir -p docs/specs docs/vision docs/constitution docs/clarify
mkdir -p docs/plan docs/modular docs/architecture
mkdir -p tests observability
mkdir -p .claude/commands

# ── Create .blueprint config ───────────────────────────────────────────────────
cat > .blueprint << EOF
BLUEPRINT_LANG=$LANG_FLAG
PROJECT_NAME=$PROJECT_NAME
BLUEPRINT_VERSION=2
EOF
echo "  ✓ .blueprint config created (LANG=$LANG_FLAG)"

# ── Create .gitignore ─────────────────────────────────────────────────────────
cat > .gitignore << 'EOF'
# Environment
.env
.env.*
!.env.example

# Python
.venv/
__pycache__/
*.pyc
*.pyo
.mypy_cache/
.ruff_cache/
.pytest_cache/

# Node
node_modules/
dist/
build/
.svelte-kit/

# Database
*.db
*.sqlite

# DCDD v2 — local-only coordination state (never commit)
.worktrees/
.context/agents/registry.local.yaml
.context/tasks/*.yaml
!.context/tasks/_task.template.yaml

# OS
.DS_Store
EOF

# ── Install git hooks ──────────────────────────────────────────────────────────
bash scripts/install_hooks.sh

# ── Create .claude/settings.json with Stop hook ───────────────────────────────
mkdir -p .claude
cat > .claude/settings.json << EOF
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python3 $(pwd)/scripts/update_docs.py 2>/dev/null || true",
        "statusMessage": "Updating living docs..."
      }]
    }]
  }
}
EOF
echo "  ✓ Claude Code Stop hook configured"

echo ""
echo "✓ $PROJECT_NAME ready at $TARGET_DIR"
echo ""
echo "Next steps:"
echo "  1. cd $PROJECT_NAME"
echo "  2. Fill in CONTEXT.md with your project description"
echo "  3. Copy .env.example to .env and set your values"
echo "  4. Open in Claude Code and run /bootstrap-app"
echo ""
echo "Auto-update hooks installed:"
echo "  → git post-commit: updates all living docs after every commit"
echo "  → Claude Code Stop: updates all living docs after every session"
echo ""
echo "Living docs updated automatically:"
echo "  → CONTEXT.md (recent changes)"
echo "  → docs/constitution/constitution.md (project status)"
echo "  → docs/clarify/assumptions.md (last review)"
echo "  → docs/plan/v1-mvp.md (build progress)"
echo "  → docs/specs/*.md (spec status markers)"
