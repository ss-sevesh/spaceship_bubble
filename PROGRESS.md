# PROGRESS.md — Spaceship Bubble Research Pipeline

**Project**: AI-driven Casimir Stiction-Suppressing Chiral Tellurium Metamaterials  
**Lead**: Sevesh SS, KEC 2028  
**Last updated**: 2026-04-11 (Session 48)

> Full session-by-session history: see `PROGRESS_ARCHIVE.md`
>
> **Auto-shrink rule**: Keep only the last 2 sessions here. When adding a new session, move the oldest one to `PROGRESS_ARCHIVE.md` first. This keeps PROGRESS.md short and token-efficient.

---

## Session 48 — Memory Cleanup + Graph Tool Full-Efficiency Protocol (Complete)

### Summary

Cleaned up memory to 3 essential files. Updated CLAUDE.md with a complete dual-tool (GitNexus + code-review-graph) full-efficiency workflow protocol. Explained blast radius results from Session 47 to user.

### Actions

| Action | Detail |
|--------|--------|
| Memory cleanup | Deleted 9 stale files (7 old feedback rules + session log + resolved bug); kept 3: user profile, PyPI setup, graph tool rule |
| CLAUDE.md updated | Replaced vague 3-bullet "Codebase Knowledge Graph" section with full 4-step dual-tool protocol (before edit, exploring, after edit, after commit) |
| Graph protocol | Both `gitnexus_impact` + `get_impact_radius` required before every edit; `npx gitnexus analyze` required after every commit |
| Blast radius reported | `casimir_energy_fast` = LOW (3 callers, 1 flow); `casimir_energy_finite_T` = CRITICAL (14 symbols, 7 callers, 4 flows) |
| PROGRESS.md | Auto-shrink rule added; Sessions 42-46 fully archived |

---

## Session 47 — Knowledge Graph Setup + PyPI v0.1.7 + Thermal Bug Fix (Complete)

### Summary

Set up full codebase knowledge graph (GitNexus + code-review-graph), fixed 3 Claude Code settings issues, ran full pre-IEEE audit, fixed classical thermal formula bug in casimir_tools tests, and published casimir-tools v0.1.7 to PyPI.

### Actions

| Action | Detail |
|--------|--------|
| GitNexus analyze | 552 nodes, 1,188 edges, 34 execution flows indexed |
| gitnexus setup | MCP + hooks configured globally for Claude Code |
| code-review-graph build | 313 nodes, 1,905 edges; auto-updates on every file edit |
| Settings fixes (3) | Removed invalid `SessionStart` + `PreCommit` hooks; fixed `timeout: 10` → `10000` |
| Full pre-IEEE audit | All 4 dimensions checked — physics constants, doc claims, UX, output fields — all pass |
| Thermal formula bug fixed | `casimir_tools/tests/test_core.py`: `/8π` → `/16π` for classical n=0 Matsubara term (DLP 1961 with weight ½); 55/55 tests passing |
| casimir-tools v0.1.7 published | Live at pypi.org/project/casimir-tools/0.1.7/ — verified install + physics |
| `.pypirc` configured | `C:\Users\11SEV\.pypirc` — future uploads fully automated |
| Draft footer updated | `docs/ieee_draft_outline.md`: v0.1.6 → v0.1.7 |

### Audit Results (Session 47)

- All physical constants match across `src/lifshitz.py`, `casimir_tools/_core.py`, CLAUDE.md, and IEEE draft ✓
- All 12 plots present and matching App.jsx PLOTS array ✓
- All pareto_results.json fields read by App.jsx present ✓
- 2-oscillator parameters consistent across all files ✓
- NSGA-II parameters (pop=50, n_gen=100, seed=42) match draft and JSON ✓

---

## Ground-Truth Physics Table (do not modify without re-running code)

| Quantity | Value |
|----------|-------|
| Te ε_⊥ | 130.86 |
| Te ε_∥ | 231.09 |
| WTe₂ ε_⊥ | 8.46 |
| WTe₂ ε_∥ | 1.56 |
| Td-WTe₂ ε_⊥ | 18.60 |
| Td-WTe₂ ε_∥ | 8.80 |
| E(Te\|WTe₂, d=10nm) | −0.1026 mJ/m² |
| E(Te\|WTe₂, d=84.2nm) | −2.44×10⁻⁴ mJ/m² |
| E(Si/Au, d=84.2nm) | −3.47×10⁻⁴ mJ/m² |
| κ_crit_sym (Te\|Te, d=10nm) | 0.7955 |
| κ_crit_sym (Te\|Te, d=84.2nm) | 0.7750 |
| κ_crit_asym (Te\|WTe₂) | 6.309 |
| CHIRAL_FACTOR (src/lifshitz.py) | 1.0 |
| CHIRAL_FACTOR (casimir_tools PyPI) | 2.0 (independently calibrated) |
| Pareto best | N=20, d=99.9nm, κ_eff=1.000, E=−1.43×10⁻⁴ mJ/m² |

---

## Current Status

| Item | Status |
|------|--------|
| Physics engine (Lifshitz + Matsubara + NSGA-II) | ✅ Complete |
| 12 publication figures (300 DPI) | ✅ Generated |
| React dashboard + FastAPI bridge | ✅ Live |
| IEEE draft | ✅ Drafted |
| SERB CRG proposal | ✅ Drafted |
| casimir-tools PyPI | ✅ v0.1.7 live |
| GitHub repo | ✅ Public |
| Tests | ✅ 124 passed |
| `master` = `origin/master` | ✅ In sync |

### Remaining (user action only)
- [ ] **Faculty co-author** — approach IIT professor (Madras/Bombay/Delhi, MEMS/nanophotonics)
- [ ] **Convert IEEE draft to LaTeX/PDF** for ScholarOne upload
