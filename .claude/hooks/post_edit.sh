#!/bin/bash
# =============================================================================
# .claude/hooks/post_edit.sh — Claude Code post-edit hook
# =============================================================================
# Runs automatically after Claude edits a file. Formats and lints any Python
# file using Ruff so issues are caught during the session, not at commit time.
#
# Exit codes:
#   0 — success or non-Python file (no action needed)
#   1 — Ruff not found (venv issue)
#   2 — lint errors found (Claude will see the output and fix them)
# =============================================================================

# Read JSON input from stdin and extract the edited file path
file_path=$(cat | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('file_path', ''))
")

# Nothing to do if no file path was provided
if [ -z "$file_path" ]; then
  exit 0
fi

# Only act on Python files — skip everything else silently
if ! echo "$file_path" | grep -qE '\.py$'; then
  exit 0
fi

RUFF="/Users/tothomas/Coding/spellforge/.venv/bin/ruff"

# Bail clearly if Ruff isn't where we expect it — likely a venv setup issue
if [ ! -x "$RUFF" ]; then
  echo "⚠ Ruff not found at $RUFF - is the venv set up?" >&2
  exit 1
fi

cd "$CLAUDE_PROJECT_DIR" || exit 1

# Format first (silent — formatting changes are not errors)
"$RUFF" format "$file_path" --quiet 2>/dev/null

# Lint and surface any errors to Claude so it can fix them immediately
lint_output=$("$RUFF" check "$file_path" 2>&1)
lint_exit=$?

if [ $lint_exit -ne 0 ]; then
  echo "$lint_output" >&2
  exit 2
fi

exit 0
