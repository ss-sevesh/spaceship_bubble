#!/usr/bin/env node
// Auto-runs `npx gitnexus analyze` after git commit or git merge
// so the GitNexus index (and CLAUDE.md tags block) stay fresh automatically.

const input = JSON.parse(process.env.CLAUDE_TOOL_INPUT || '{}');
const command = (input.command || '').toLowerCase();

const isCommit = command.includes('git commit');
const isMerge  = command.includes('git merge');

if (!isCommit && !isMerge) process.exit(0);

const { execSync } = require('child_process');
const path = require('path');

const projectDir = path.resolve(__dirname, '..', '..');

try {
  console.log('[gitnexus] commit detected — re-indexing codebase...');
  execSync('npx gitnexus analyze', { cwd: projectDir, stdio: 'inherit' });
  console.log('[gitnexus] index updated ✓');
} catch (e) {
  console.error('[gitnexus] analyze failed:', e.message);
  // Non-fatal — don't block the commit
}
