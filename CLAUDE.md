# CLAUDE.md — Spaceship Bubble Research Project

## Project Identity

| Field | Value |
|-------|-------|
| **Title** | AI-driven Casimir Stiction-Suppressing Chiral Tellurium Metamaterials |
| **Lead** | Sevesh SS, KEC 2028 |
| **Goals** | IEEE publication + SERB funding application |
| **Status** | Active development (April 2026) |

---

## Physics Context

### Problem
Stiction — adhesion caused by Casimir/van der Waals forces at nanoscale gaps — is a primary failure mode in MEMS/NEMS devices.

### Approach
Use chiral Tellurium (Te) metamaterials to engineer the dielectric response such that the Casimir force becomes **repulsive or minimized**.

---

## Stack

### Core Physics (Python)
- **uv** (package manager)
- **pymatgen** / **mp-api** (Materials Project)
- **scipy** / **numpy** (Lifshitz integration)
- **pymoo** (NSGA-II multi-objective optimization)
- **fastapi** / **uvicorn** (Backend Bridge API)

### Dashboard (React)
- **Vite** (Build tool)
- **Three.js** / **@react-three/fiber** (3D Visualization)
- **Framer Motion** (Kinetic UI & Staggered Animations)
- **Lucide React** (Iconography)

---

## Project Structure

```
spaceship_bubble/
├── CLAUDE.md
├── PROGRESS.md
├── README.md
├── main.py                <- Entry point / orchestrator
├── sync_assets.py         <- Syncs plots/ and outputs/ to dashboard/public/
├── analyze.py             <- Quick Pareto results analysis utility
├── pyproject.toml         <- Project dependencies (uv)
├── data/                  <- DFT dielectric JSON (tellurium, wte2, td_wte2_dft)
├── outputs/               <- NSGA-II output (pareto_results.json)
├── plots/                 <- Generated publication figures (12 PNGs, 300 DPI)
├── docs/                  <- ieee_draft_outline.md, serb_proposal_draft.md, cover_letter.md
├── tests/                 <- Physics unit tests (test_lifshitz.py)
├── casimir_tools/         <- PyPI package (pip install casimir-tools, v0.1.6)
├── dashboard/             <- React Research Dashboard (Vite)
│   ├── server.py          <- FastAPI Backend Bridge (Port 8000)
│   ├── LAUNCH.md          <- Deployment instructions
│   ├── index.html         <- Entry HTML (title: Spaceship Bubble)
│   └── src/
│       ├── components/
│       │   └── CasimirScene.jsx <- 3D Fiber Visualizer
│       └── App.jsx        <- Dashboard Engine
└── src/                   <- Core Python Logic
    ├── lifshitz.py        <- Casimir physics engine
    ├── optimizer.py       <- NSGA-II 3-objective optimizer
    ├── visualize.py       <- 12 plot generators
    └── fetch_materials.py <- Materials Project API fetch
```

---

## Current Status Checklist

- [x] Lifshitz TE+TM double integral (Cauchy model)
- [x] Chiral correction (kappa^2 term)
- [x] NSGA-II Pareto Optimization (50 solutions)
- [x] Casimir force F = -dE/dd analytical curves
- [x] Anisotropic uniaxial dielectric tensor model
- [x] IEEE draft & SERB CRG proposal drafted
- [x] **FastAPI Backend Bridge** (Live Sync enabled)
- [x] **3D Fiber Visualizer** (Metamaterial geometry)
- [x] **Triple-A Immersive UI** (Particle Background & Kinetic Text)
- [x] **Finite-T Casimir** (Matsubara summation, T=300 K, `casimir_finite_T.png`)
- [x] **2-oscillator Sellmeier model** (IR phonon + UV electronic, `casimir_2osc_model.png`)
- [x] **3-objective NSGA-II** (F3 = thermal_fraction, dual-panel Pareto plot)
- [x] **Td-WTe₂ substrate** (DFT-HSE06 tensor, ε_⊥=18.60, ε_∥=8.80, `casimir_td_wte2.png`)
- [x] **casimir-tools PyPI package** (v0.1.6 live — pypi.org/project/casimir-tools/)
- [x] **Download Report** (exports selected Pareto design as `.txt` with full metadata)

---

## Physical Constants (SI)

```python
HBAR = 1.0545718e-34   # J·s
KB   = 1.380649e-23    # J/K
C    = 2.99792458e8    # m/s
```

---

## Audit Protocol (MANDATORY — never skip)

When asked "is this ready?", "check everything", or any publication/submission audit:

**NEVER trust PROGRESS.md ✓ marks as proof of correctness.** They record what was believed at the time — not current state.

### Required cross-checks before any "ready" verdict

1. **Code → Draft numeric parity**: For every constant, factor, or table in `docs/ieee_draft_outline.md`, grep the live value from the actual source file and compare directly.
   ```
   grep CONSTANT src/lifshitz.py          # get live value
   grep CONSTANT docs/ieee_draft_outline.md  # get claimed value
   # if different → flag immediately
   ```

2. **All four audit dimensions** (non-negotiable):
   - Physics values (constants, prefactors, table numbers)
   - Doc claims vs live code (draft numbers match what code actually computes)
   - UX simulation (dashboard renders correctly)
   - Output field tracing (pareto_results.json fields match what App.jsx reads)

3. **Every directory** — not just `src/`: also `docs/`, `casimir_tools/`, `dashboard/`, `tests/`, `pyproject.toml`, `README.md`

4. **Primary sources only** — open the actual files side by side. PROGRESS.md is a log, not a truth table.

---

# Codebase Knowledge Graph — Full Efficiency Protocol

This project has TWO graph tools. Use BOTH. They complement each other.

| Tool | Index | Best for |
|------|-------|----------|
| **GitNexus** | Manual — run `npx gitnexus analyze` after every commit | Deep blast radius, execution flow tracing, safe rename |
| **code-review-graph** | Auto — updates after every Edit/Write/Bash | Quick structural impact, callers/callees, post-edit confirmation |

## Mandatory Workflow for Every Code Change

### Step 1 — Before touching ANY symbol (function, class, constant):
1. `gitnexus_impact({target: "symbolName", direction: "upstream", includeTests: true})` — blast radius + risk level
2. `get_impact_radius({symbol: "symbolName"})` — structural callers/callees from code-review-graph
3. Report both results to user — if either returns HIGH or CRITICAL, warn before proceeding
4. If chain is 3+ levels deep → enter plan mode first

### Step 2 — Before exploring unfamiliar code (use graph, NOT Grep):
- `gitnexus_query({query: "concept"})` — finds execution flows by concept, ranked by relevance
- `semantic_search_nodes({query: "keyword"})` — finds functions/classes by name or keyword
- `gitnexus_context({name: "symbolName"})` — full 360° view: callers, callees, which flows it's in
- `query_graph({pattern: "callers_of", target: "X"})` — structural relationships
- Fall back to Grep/Glob/Read ONLY when graph doesn't cover it

### Step 3 — After the edit:
- `gitnexus_detect_changes({scope: "staged"})` — confirms only expected symbols changed
- code-review-graph auto-updates (no action needed)

### Step 4 — After every commit:
```bash
npx gitnexus analyze
```
GitNexus goes stale after commits. A stale index = wrong blast radius on next change.
If embeddings exist: `npx gitnexus analyze --embeddings`

## Never Do
- NEVER use Grep to explore code when graph tools can answer it
- NEVER edit a symbol without running BOTH blast radius checks first
- NEVER rename with find-and-replace — use `gitnexus_rename` (understands call graph)
- NEVER commit without `gitnexus_detect_changes()` confirming scope
- NEVER ignore HIGH or CRITICAL risk warnings

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **spaceship_bubble** (557 symbols, 1192 relationships, 34 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/spaceship_bubble/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/spaceship_bubble/context` | Codebase overview, check index freshness |
| `gitnexus://repo/spaceship_bubble/clusters` | All functional areas |
| `gitnexus://repo/spaceship_bubble/processes` | All execution flows |
| `gitnexus://repo/spaceship_bubble/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
