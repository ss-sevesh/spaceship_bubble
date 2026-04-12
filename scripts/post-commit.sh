#!/usr/bin/env bash
# post-commit hook — smart re-index + CLAUDE.md sync + auto-push
#
# Install: cp scripts/post-commit.sh .git/hooks/post-commit && chmod +x .git/hooks/post-commit
# Or run:  sh setup.sh

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"

# ── Recursion guard (file-based, env vars don't survive child processes) ──────
LOCK="$ROOT/.git/gitnexus_hook.lock"
if [ -f "$LOCK" ]; then exit 0; fi
touch "$LOCK"
trap 'rm -f "$LOCK"' EXIT

# ── Did this commit touch any Python files? ───────────────────────────────────
PY_CHANGED=0
if git diff-tree --no-commit-id -r --name-only HEAD 2>/dev/null | grep -q '\.py$'; then
    PY_CHANGED=1
fi

if [ "$PY_CHANGED" = "1" ]; then
    # 1. Re-index GitNexus
    echo "[post-commit] Python files changed — re-indexing GitNexus..."
    if ! npx gitnexus analyze "$ROOT" --quiet 2>/dev/null; then
        npx gitnexus analyze "$ROOT" || { echo "[post-commit] ERROR: gitnexus analyze failed"; exit 1; }
    fi
    echo "[post-commit] GitNexus index updated ✓"

    # 2. Sync CLAUDE.md from live values
    if python "$ROOT/scripts/update_claude_md.py"; then
        echo "[post-commit] CLAUDE.md synced ✓"
    else
        echo "[post-commit] ERROR: update_claude_md.py failed"
        exit 1
    fi

    # 3. If CLAUDE.md or AGENTS.md changed, amend them into the commit
    DOCS_CHANGED=0
    git -C "$ROOT" diff --quiet CLAUDE.md  2>/dev/null || { git -C "$ROOT" add CLAUDE.md;  DOCS_CHANGED=1; }
    git -C "$ROOT" diff --quiet AGENTS.md  2>/dev/null || { git -C "$ROOT" add AGENTS.md;  DOCS_CHANGED=1; }
    if [ "$DOCS_CHANGED" = "1" ]; then
        git commit --amend --no-edit --no-verify
        echo "[post-commit] CLAUDE.md + AGENTS.md auto-patched into commit ✓"
    fi
else
    echo "[post-commit] No Python files changed — skipping re-index"
fi

# ── Auto-push to origin ───────────────────────────────────────────────────────
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if git remote get-url origin &>/dev/null; then
    if git push origin "$BRANCH" --quiet 2>/dev/null; then
        echo "[post-commit] pushed to origin/$BRANCH ✓"
    else
        echo "[post-commit] push failed (offline or diverged) — commit saved locally"
    fi
fi
