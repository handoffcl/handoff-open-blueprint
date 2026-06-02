#!/bin/bash
echo "Installing AI App Blueprint..."
mkdir -p ~/.claude/commands
cp commands/bootstrap-app.md ~/.claude/commands/
echo "✓ Done. Use /bootstrap-app in any Claude Code session."
