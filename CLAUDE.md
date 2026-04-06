# CLAUDE.md — Spaceship Bubble Research Project

## Project Identity

| Field | Value |
|-------|-------|
| **Title** | AI-driven Casimir Stiction-Suppressing Chiral Tellurium Metamaterials |
| **Lead** | Sevesh SS, KEC 2026 |
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
├── main.py                <- Entry point / orchestrator
├── sync_assets.py         <- Syncs data to dashboard/public
├── dashboard/             <- React Research Dashboard (Vite)
│   ├── server.py          <- FastAPI Backend Bridge (Port 8000)
│   ├── LAUNCH.md          <- Deployment instructions
│   └── src/
│       ├── components/
│       │   └── CasimirScene.jsx <- 3D Fiber Visualizer
│       └── App.jsx        <- Dashboard Engine
└── src/                   <- Core Python Logic (lifshitz, optimizer, etc.)
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
