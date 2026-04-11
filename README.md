# Spaceship Bubble

**AI-driven Casimir Stiction-Suppressing Chiral Tellurium Metamaterials**  
Lead: Sevesh SS, KEC 2028 | Target: IEEE Transactions on Nanotechnology + SERB CRG

[![DOI](https://zenodo.org/badge/1202645604.svg)](https://doi.org/10.5281/zenodo.19517866)
[![PyPI version](https://img.shields.io/pypi/v/casimir-tools)](https://pypi.org/project/casimir-tools/)

---

## What This Is

A full-stack physics research pipeline that:

1. Fetches DFT dielectric tensors from Materials Project (Te mp-19, WTe₂ mp-1023926)
2. Computes Lifshitz-Casimir energy and force for chiral uniaxial heterostructures
3. Runs NSGA-II multi-objective optimization to find stiction-minimizing designs
4. Visualizes results in an immersive React dashboard with 3D metamaterial renderer

The physics engine implements:
- Zero-temperature Lifshitz double integral (TE + TM, uniaxial Fresnel coefficients)
- Chiral κ² correction (Zhao et al. 2009)
- Finite-temperature Matsubara summation (T = 300 K, classical n=0 term)
- Two-oscillator Sellmeier dielectric model (IR phonon + UV electronic)
- Td-WTe₂ Weyl semimetal phase (DFT-HSE06 dielectric tensor)
- 3-objective NSGA-II: minimize |E_Casimir|, device thickness, thermal fraction f_T

---

## Quickstart

```bash
# Install dependencies
uv sync

# Run full pipeline (fetch → lifshitz check → optimize → plot → sync dashboard)
uv run python main.py --all

# Or step by step:
uv run python main.py --fetch        # Step 1: fetch Materials Project data
uv run python main.py --lifshitz     # Step 2: Lifshitz sanity check table
uv run python main.py --optimize     # Step 3: NSGA-II + auto-sync to dashboard
uv run python main.py --plot         # Step 4: generate all 12 plots

# Td-WTe₂ substrate variant:
OPTIMIZER_SUBSTRATE=td uv run python main.py --optimize
```

---

## Dashboard

```bash
# Terminal 1 — FastAPI backend (port 8000)
cd dashboard && uv run python server.py

# Terminal 2 — React dev server (port 5173)
cd dashboard && npm install && npm run dev
```

Open http://localhost:5173. The dashboard shows:
- 3D metamaterial visualizer (React Three Fiber)
- Pareto-optimal design table with thermal fraction column
- 12-plot gallery (Casimir curves, aniso, chiral, force, Pareto, finite-T, 2-osc, Td-WTe₂, Au/SiO₂ benchmark)
- "Re-Optimize" button triggers `main.py --optimize --plot` via FastAPI, polls `/api/status` every 3s, and live-syncs results when complete
- Download Report exports selected Pareto design as a `.txt` spec file

---

## Project Structure

```
spaceship_bubble/
├── main.py                   # Pipeline orchestrator (--fetch/--lifshitz/--optimize/--plot/--all)
├── sync_assets.py            # Syncs plots/ and outputs/ to dashboard/public/
├── src/
│   ├── lifshitz.py           # Core physics: Lifshitz integrals, chiral/aniso/2osc/finite-T
│   ├── optimizer.py          # NSGA-II 3-objective optimizer (pymoo)
│   ├── visualize.py          # 12 plot generators
│   └── fetch_materials.py    # Materials Project API fetch
├── data/                     # JSON dielectric data (Te, WTe₂, Td-WTe₂)
├── outputs/                  # pareto_results.json (NSGA-II output)
├── plots/                    # Generated PNG plots
├── dashboard/
│   ├── server.py             # FastAPI bridge (port 8000)
│   ├── src/
│   │   ├── App.jsx           # Dashboard engine
│   │   └── components/CasimirScene.jsx  # 3D visualizer
│   └── public/               # Synced assets (served by Vite)
├── casimir_tools/            # PyPI-ready package (pip install casimir-tools)
├── docs/
│   ├── ieee_draft_outline.md    # IEEE Trans. Nanotechnology draft
│   ├── serb_proposal_draft.md   # SERB CRG proposal draft
│   ├── submission_checklist.md  # Pre-submission verification checklist
│   └── cover_letter.md          # Journal cover letter (GitHub URL filled)
└── PROGRESS.md               # Session-by-session progress log
```

---

## Key Results

| Result | Value |
|--------|-------|
| Pareto-optimal design (hex WTe₂) | N=20 layers, d=99.9 nm, κ_eff=0.937, E=−1.44×10⁻⁴ mJ/m² |
| Best Te/Te stiction reduction | ~40% at κ_eff=0.5; zero force at κ_crit≈0.795 (d=10nm) |
| Te/WTe₂ chiral correction (asymmetric) | ≈3% max (κ_crit_asym≈6.3, unphysical) |
| WTe₂ anisotropy passive suppression | 14% TM-mode reduction (independent of chirality) |
| Td-WTe₂ vs hex-WTe₂ Casimir coupling | ~2× stronger (ratio 2.01 at d=1 nm, 1.45 at d=53 nm) |
| Thermal fraction — hex WTe₂ substrate | f_T = 0.003–173 across Pareto front; balanced design (κ_eff=0.937, d≈99.9nm) has f_T=0.023; min-stiction designs (κ_eff=1.000) have f_T=10–173 |
| Thermal fraction — Td-WTe₂ substrate | f_T ≈ 0.98 at d=63 nm (thermally dominated; large ε_∥=8.80) |
| Quantum-classical crossover | l_T = ħc/2k_BT = 1215 nm at T=300 K → crossover at d ~ 193 nm |

---

## Physical Constants (SI)

```python
HBAR = 1.0545718e-34   # J·s
KB   = 1.380649e-23    # J/K
C    = 2.99792458e8    # m/s
```

---

## casimir-tools Package

```bash
pip install casimir-tools
pip install "casimir-tools[plot]"   # with matplotlib
```

```python
import casimir_tools as ct

E        = ct.casimir_energy(eps_static1=164.27, eps_static2=6.16, d=10e-9)
E_chiral = ct.casimir_energy_chiral(eps_static1=164.27, eps_static2=6.16, d=10e-9, kappa=0.5)
d_nm, F  = ct.sweep_force(eps1=164.27, eps2=6.16, d_min_nm=5.0, d_max_nm=100.0, n_points=100)
```

[![PyPI version](https://img.shields.io/pypi/v/casimir-tools)](https://pypi.org/project/casimir-tools/) — live on PyPI.

---

## References

1. Lifshitz (1956) Sov. Phys. JETP 2, 73
2. Zhao et al. (2009) PRL 103, 103602 — chiral Casimir
3. Bimonte et al. (2009) PRA 79, 042906 — uniaxial Lifshitz
4. Deb et al. (2002) IEEE Trans. Evol. Comp. 6, 182 — NSGA-II
5. Caldwell & Fan (1959) PR 114, 664 — Te IR phonon
6. Stuke (1965) Phys. Status Solidi 8, 533 — Te UV electronic
