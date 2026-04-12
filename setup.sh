#!/usr/bin/env bash
# setup.sh — one-command fresh clone install for spaceship_bubble
# Usage: sh setup.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "==> spaceship_bubble setup"
echo "    root: $ROOT"

# ── Dependency checks ─────────────────────────────────────────────────────────
warn() { echo "[warn] $*"; }

check_cmd() {
    if ! command -v "$1" &>/dev/null; then
        warn "$1 not found — $2"
        return 1
    fi
    return 0
}

HAS_NPX=1; HAS_UV=1; HAS_PYTHON=1
check_cmd npx    "install Node.js from https://nodejs.org"   || HAS_NPX=0
check_cmd uv     "install uv from https://docs.astral.sh/uv" || HAS_UV=0
check_cmd python "install Python 3.11+"                      || HAS_PYTHON=0

# ── 1. Install git post-commit hook ──────────────────────────────────────────
echo ""
echo "==> Installing post-commit hook..."
cp "$ROOT/scripts/post-commit.sh" "$ROOT/.git/hooks/post-commit"
chmod +x "$ROOT/.git/hooks/post-commit"
echo "    ✓ .git/hooks/post-commit installed"

# ── 2. Python dependencies ───────────────────────────────────────────────────
if [ "$HAS_UV" = "1" ]; then
    echo ""
    echo "==> Installing Python dependencies (uv sync)..."
    uv sync --all-groups
    echo "    ✓ dependencies installed"
else
    warn "uv not found — skipping Python dependency install"
fi

# ── 3. GitNexus — build index ────────────────────────────────────────────────
if [ "$HAS_NPX" = "1" ]; then
    echo ""
    echo "==> Indexing codebase with GitNexus..."
    npx gitnexus analyze "$ROOT"
    echo "    ✓ GitNexus index built"
else
    warn "npx not found — skipping GitNexus index (run 'npx gitnexus analyze' manually)"
fi

# ── 4. code-review-graph — build graph ───────────────────────────────────────
# Note: 'build' has a known upstream sqlite bug; 'update' is the working equivalent
if [ "$HAS_PYTHON" = "1" ]; then
    echo ""
    echo "==> Building code-review-graph..."
    (cd "$ROOT" && python -m code_review_graph update --skip-flows) 2>/dev/null || \
        warn "code-review-graph update failed — run 'python -m code_review_graph update --skip-flows' manually"
    echo "    ✓ code-review-graph built"
else
    warn "python not found — skipping code-review-graph build"
fi

# ── 5. Sync CLAUDE.md + AGENTS.md ────────────────────────────────────────────
echo ""
echo "==> Syncing CLAUDE.md + AGENTS.md..."
python "$ROOT/scripts/update_claude_md.py" && echo "    ✓ docs up to date"

echo ""
echo "==> Setup complete."
echo "    Next: open Claude Code in this directory — both MCPs will be active."
